from __future__ import print_function
# Libraries needed for Twitter API
import tweepy, time, json
# Libraries needed for File Management
import sys, os, requests, io
# Libraries needed for Google Drive API
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from googleapiclient.http import MediaIoBaseUpload

#################
# Configuration #
################# 
HASHTAG = 'NintendoSwitch'  # Generic hashtag that Nintendo Switch always put in the tweets
USERNAME = 'your-user-name'          # The account where you will share the media
LOCAL_FLAG = False       # True if you want to save the images locally
CLOUD_FLAG = True          # True if you want to upload the photos to Google Drive
TWEETS = 15                  # Number of tweets written by the account, including the ones that doesn't have 
                            # the desired hashtag


##################
##################
##################


class TwitterAPI:
    def read_credentials(self):
        with open('creds/twitterAPI.json') as json_file:
            creds = json.load(json_file)
        return creds
    
    def get_api_auth(self):
        try:
            creds = TwitterAPI().read_credentials()
            consumer_key = creds['consumer_key']
            consumer_secret = creds['consumer_secret'] 
            access_token = creds['access_token']
            access_secret = creds['access_secret']
        except KeyError:
            sys.stderr.write('TWITTER_ * environment variable not set')
            sys.exit(1)
        
        auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
        auth.set_access_token(access_token,access_secret)
        return auth

    # Authentication into Twitter
    def get_twitter_client(self):
        auth = self.get_api_auth()
        client = tweepy.API(auth, wait_on_rate_limit=True)
        return client

    # Get a JSON with all the tweets' requested data
    def get_user_timeline(self, client):
        try: 
            # Pulling individual tweets from query
            for tweet in client.user_timeline(id=USERNAME, count= TWEETS, include_rts=False): # Adding to the list that contains all tweets
                tweets.append((tweet.created_at,tweet.id,tweet.text, tweet.entities, tweet.extended_entities))  # This line throws an exception if a
                                                                                                                # tweet doesn't have media in it
        except BaseException as e:
            print('failed on_status,',str(e))
            time.sleep(3)
        return tweets

    # Get the url and media type from the JSON
    def get_media_info_from_tweet(self, tweet,urls, media_type):
        t = tweet[4]['media'][0]['type']
        if t == 'photo':
            u = tweet[4]['media'][0]['media_url_https']
        else:
            u = tweet[4]['media'][0]['video_info']['variants'][3]['url']
        urls.append(u)
        media_type.append(t)
        return urls, media_type

    
    def get_tweets_hashtag(self, tweet_list):
        urls = []
        media_type = []
        for i in range(0, len(tweet_list)):
            tweet = tweet_list[i]
            hashtag_list = tweet[3]['hashtags'] # Get the hashtag list
            if hashtag_list: # If hashtag list is not empty 
                for k in range(0, len(hashtag_list)):  # Search in the hashtag list the wanted hashtag
                    ht = hashtag_list[k]['text']
                    if ht == HASHTAG:
                        [urls, media_type] = self.get_media_info_from_tweet(tweet,urls,media_type)                
        return urls, media_type

class DriveAPI:
    def connect(self):
        try :
            import argparse
            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None
        SCOPES = 'https://www.googleapis.com/auth/drive.file'
        store = file.Storage('creds/storage.json')
        creds = store.get()
        if not creds or creds.invalid:
            print('make new storage data file ')
            flow = client.flow_from_clientsecrets('creds\client_secret.json', SCOPES)
            creds = tools.run_flow(flow, store, flags) \
                    if flags else tools.run_flow(flow, store)
        service = build('drive', 'v3', http=creds.authorize(Http()))
        return service

    def search_folder(self,service):
        page_token = None
        while True:
            response = service.files().list(q="mimeType='application/vnd.google-apps.folder' and name='Switch Captures'",
                                                spaces='drive',
                                                fields='nextPageToken, files(id, name)',
                                                pageToken=page_token).execute()
            
            folder_list = response.get('files', [])
            if page_token is None:
                break
        if folder_list:
            folder_id = folder_list[0].get('id')
            return folder_id

    def create_folder(self, service):
        file_metadata = {
            'name': 'Switch Captures',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        service.files().create(body=file_metadata, fields='id').execute()

    def routine_folder(self, service):
        print('Searching "Switch Captures" folder on Google Drive...')
        folder_id = self.search_folder(service)
        while not folder_id:
            print('Folder not found. Creating folder...')
            self.create_folder(service)
            folder_id = self.search_folder(service)
        print('Folder created.')
        return folder_id

    def search_file(self, service, file_name):
        page_token = None
        query = "name='" + file_name +"'"
        while True:
            response = service.files().list(q= query,
                                            spaces='drive',
                                            fields='nextPageToken, files(id, name)',
                                            pageToken=page_token).execute()
            file_list = response.get('files', [])
            if page_token is None:
                break
        if file_list:
            return True
        else:
            return False
    
    def _get_file_type(self, file_name):
        f = file_name[file_name.rfind('.')+1:len(file_name)]
        if f == 'jpg' or f == 'jpeg':
            file_type = 'photo'
        elif f == 'mp4':
            file_type = 'video'
        return file_type

    def get_IOBase_content(self, url):
        r = requests.get(url)
        f = io.BytesIO(r.content)
        return f 

    def _photo_file_upload(self, f_io):
        media = MediaIoBaseUpload(f_io, mimetype='image/jpeg')
        return media
    
    def _video_file_upload(self, f_io):
        media = MediaIoBaseUpload(f_io, mimetype='video/mp4')
        return media

    def upload_file(self, service, file_name, f_io, folder_id):
        file_metadata = {'name': file_name,
                         'parents': [folder_id]}
        file_type = self._get_file_type(file_name)
        if file_type == 'photo':
            media = self._photo_file_upload(f_io)
        elif file_type == 'video':
            media = self._video_file_upload(f_io)
        file = service.files().create(body=file_metadata, media_body=media).execute()
        return file
    

class FileManagement:
    def get_filename_photo(self, url):
        name = url[url.rfind('/')+1:len(url)]
        return name

    def get_filename_video(self, url):
        name = url[url.rfind('/')+1:url.rfind('.')+4]
        return name
    
    def get_file_name(self, url, Type):
        if Type == 'photo':
                file_name = self.get_filename_photo(url)
        elif Type == 'video':
                file_name = self.get_filename_video(url)
        return file_name

    def download_media(self, media_links, media_type):
        for i in range(0,len(media_links)):
            url = media_links[i]
            Type = media_type[i]
            file_name = self.get_file_name(url,Type)
            r = requests.get(url, allow_redirects=True)
            file_path = 'media/'+ file_name
            open(file_path, 'wb').write(r.content)

#################
# Main function #
#################

if __name__ == '__main__':
    print('------Twitter-Switch-Share------\n\n\n')
    tweets = []
    media = []
    if CLOUD_FLAG:
        drive = DriveAPI().connect()
    # Get twitter access
    client = TwitterAPI().get_twitter_client()
    print('Twitter Access granted!')
    # Retrieve tweets
    print('Retrieving tweets from: %s...' % USERNAME)
    tweets = TwitterAPI().get_user_timeline(client)
    # Search for '#NintendoSwitch'
    print('Searching for #%s...' % HASHTAG)
    [media_links, media_types] = TwitterAPI().get_tweets_hashtag(tweets)
    if LOCAL_FLAG:
        print('Downloading media locally')
        FileManagement().download_media(media_links, media_types)
        print('Files downloaded! You will find them in /media')
    if CLOUD_FLAG:
        print('Accessing Google Drive API')
        # drive = DriveAPI().connect() this line is commente because a strange error in the first execution.
        print('Google Drive access granted!')
        print('Looking for a folder called "Switch Captures" on your Drive. In case you do not have it, it will be automatically created')
        folder_id = DriveAPI().routine_folder(drive)
        print('Uploading media...')
        for i in range(0, len(media_links)):
            url = media_links[i]
            Type = media_types[i]
            file_name = FileManagement().get_file_name(url,Type)
            if DriveAPI().search_file(drive, file_name):
               print('%s is already uploaded, trying with next file.' % file_name)
               pass 
            else:
                print('Uploading %s...' % file_name)
                f_io = DriveAPI().get_IOBase_content(url)
                DriveAPI().upload_file(drive, file_name, f_io, folder_id)
                print('%s uploaded' % file_name)

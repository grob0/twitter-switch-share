from __future__ import print_function

from Twitter import TwitterAPI
from Google import DriveAPI
from FileManagement import Local

#################
# Configuration #
################# 

# HASHTAG = 'NintendoSwitch'    # Generic hashtag that Nintendo Switch always put in the tweets
USERNAME = 'your-user-name'     # The account where you will share the media
LOCAL_FLAG = False              # True if you want to save the images locally
CLOUD_FLAG = True               # True if you want to upload the photos to Google Drive
TWEETS = 20                     # Number of tweets written by the account, including the ones that doesn't have 
                                # the desired hashtag

# Drive configuration
DRIVE_FOLDER_NAME = 'Switch Captures'


if __name__ == '__main__':
    print('------Twitter-Switch-Share------\n\n\n')
    media = []
    twAPI = TwitterAPI()
    # Get twitter access
    tw_client = twAPI.get_twitter_client()
    print('Twitter Access granted!')
    # Retrieve tweets
    print('Retrieving tweets from: %s...' % USERNAME)
    tweets = twAPI.get_user_timeline(tw_client,USERNAME,TWEETS)
    # Search for '#NintendoSwitch'
    print('Searching for tweets sent from Nintendo Switch Share')
    [media_links, media_types] = twAPI.get_tweets_nss(tweets)
    localAPI = Local()
    if len(media_links) > 0:
        if LOCAL_FLAG:
            print('Downloading media locally')
            localAPI.download_media(media_links, media_types)
            print('Files downloaded! You will find them in /media')
        if CLOUD_FLAG:
            gdAPI = DriveAPI()
            print('Accessing Google Drive API')
            drive_client = gdAPI.connect()
            print('Google Drive access granted!')
            print('Looking for a folder called "' + DRIVE_FOLDER_NAME + '" on your Drive. In case you do not have it, it will be automatically created')
            folder_id = gdAPI.routine_folder(drive_client, DRIVE_FOLDER_NAME)
            print('Uploading media...')
            for i in range(0, len(media_links)):
                url = media_links[i]
                Type = media_types[i]
                file_name = localAPI.get_file_name(url,Type)
                if gdAPI.search_file(drive_client, file_name):
                    print('%s is already uploaded, trying with next file.' % file_name)
                    pass 
                else:
                    print('Uploading %s...' % file_name)
                    f_io = gdAPI.get_IOBase_content(url)
                    gdAPI.upload_file(drive_client, file_name, f_io, folder_id)
    else:
        print('Some exception retrieving your Twitter Media. Sorry about that, please inform my creator :)')
        print('www.github.com/gruizmudarra/twitter-switch-share')
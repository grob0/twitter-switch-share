import sys
from tweepy import OAuthHandler, API
from json import load
from time import sleep

# Contains relevant info about a media tweet
class MediaTweet:
    def __init__(self, date, id, text, entities, extended_entities, source):
        self.date = date
        self.id = id
        self.text = text
        self.entities = entities
        self.extended_entities = extended_entities
        self.source = source

class TwitterAPI:
    def _read_credentials(self):
        with open('creds/twitterAPI.json') as json_file:
            creds = load(json_file)
        return creds
    
    def _get_api_auth(self):
        try:
            creds = TwitterAPI()._read_credentials()
            consumer_key = creds['consumer_key']
            consumer_secret = creds['consumer_secret'] 
            access_token = creds['access_token']
            access_secret = creds['access_secret']
        except KeyError:
            sys.stderr.write('TWITTER_ * environment variable not set')
            sys.exit(1)
        
        auth = OAuthHandler(consumer_key,consumer_secret)
        auth.set_access_token(access_token,access_secret)
        return auth

    # Authentication into Twitter
    def get_twitter_client(self):
        auth = self._get_api_auth()
        client = API(auth, wait_on_rate_limit=True)
        return client

    # Get a JSON with all the tweets' requested data
    def get_user_timeline(self, client, username, tweet_count):
        tweets = []

        # Pulling individual tweets from query
        for tweet in client.user_timeline(id=username, count= tweet_count, include_rts=False): # Adding to the list that contains all tweets
            if hasattr(tweet, 'extended_entities'):
                tweets.append(MediaTweet(tweet.created_at, tweet.id, tweet.text, tweet.entities, tweet.extended_entities, tweet.source))

        return tweets

    # Get the url and media type from the JSON
    def _get_media_info_from_tweet(self, tweet, urls, media_type):
        media_list = tweet.extended_entities['media']
        for media in media_list:
            t = media['type']
            if t == 'photo':
                u = media['media_url_https']
            else:
                variants = media['video_info']['variants']
                max_bitrate = -1
                for variant in variants:
                    bitrate = variant.get('bitrate')
                    if bitrate and bitrate > max_bitrate:
                        max_bitrate = bitrate
                        u = variant['url']
            urls.append(u)
            media_type.append(t)
        return urls, media_type

    def get_tweets_hashtag(self, tweet_list, hashtag): # This is not used right now
        urls = []
        media_type = []
        for tweet in tweet_list:
            hashtag_list = tweet.entities['hashtags'] # Get the hashtag list
            if hashtag_list: # If hashtag list is not empty 
                for k in range(0, len(hashtag_list)):  # Search in the hashtag list the wanted hashtag
                    ht = hashtag_list[k]['text']
                    if ht == hashtag:
                        [urls, media_type] = self._get_media_info_from_tweet(tweet,urls,media_type)                
        return urls, media_type

    def get_tweets_nss(self, tweet_list):
        urls = []
        media_type = []
        for tweet in tweet_list:
            source = tweet.source
            if 'Nintendo Switch Share' in source: # If source is Nintendo Switch Share
                [urls, media_type] = self._get_media_info_from_tweet(tweet,urls,media_type)                
        return urls, media_type

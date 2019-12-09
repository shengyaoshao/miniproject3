from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import sys
from textblob import TextBlob
import io
import twitter_credentials
import urllib.request
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import os
import mysql
import mysql.connector


class TwitterClient():
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_friend_list(self, num_friends):
        friend_list = []
        for friend in Cursor(self.twitter_client.friends, id=self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list

    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline, id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets
       
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        auth = OAuthHandler("WlB4qdecgNZH7TSkuRQWGKYz4", "EDimeHCtpxilJeoXncgT0XPtXMJOzmQAjiG5VbnG4ytXyWbcu9")
        auth.set_access_token("1173709326113890304-zh4X45gok1LlFx41BuvhB6EJ5hYsfh", "eWIKD8RFr8VaLtbu1NiLOtKu4iEkYrrPTvQwA7rBLOd5M")
        return auth
class TwitterStreamer():
    """
    Class for streaming and processing live tweets.
    """
    def __init__(self):
        self.twitter_autenticator = TwitterAuthenticator()    

    def stream_tweets(self, fetched_tweets_filename, hash_tag_list):
        # This handles Twitter authetification and the connection to Twitter Streaming API
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_autenticator.authenticate_twitter_app() 
        stream = Stream(auth, listener)

        # This line filter Twitter Streams to capture data by the keywords: 
        stream.filter(track=hash_tag_list)


# # # # TWITTER STREAM LISTENER # # # #
class TwitterListener(StreamListener):
    """
    This is a basic listener that just prints received tweets to stdout.
    """
    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweets_filename, 'a') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print("Error on_data %s" % str(e))
        return True
          
    def on_error(self, status):
        if status == 420:
            # Returning False on_data method in case rate limit occurs.
            return False
        print(status)


class TweetAnalyzer():

    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))
        
        if analysis.sentiment.polarity > 0:
            return 'positive'
        elif analysis.sentiment.polarity == 0:
            return 'neutral'
        else:
            return 'negative'

    def tweets_to_data_frame(self, tweets):
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets'])

        df['id'] = np.array([tweet.id for tweet in tweets])
        df['date'] = np.array([tweet.created_at for tweet in tweets])
        df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
        df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])

        return df

 
if __name__ == '__main__':
    vantage = mysql.connector.connect(host = "localhost", user = "root", password = "4396",auth_plugin='mysql_native_password',database = 'db9')
    mycursor = vantage.cursor()
    twitter_client = TwitterClient()
    tweet_analyzer = TweetAnalyzer()

    api = twitter_client.get_twitter_client_api()
    print('Enter the Twitter account name')
    screen_name = input()
    tweets = api.user_timeline(screen_name, count=200)
    df = tweet_analyzer.tweets_to_data_frame(tweets)
    df['sentiment'] = np.array([tweet_analyzer.analyze_sentiment(tweet) for tweet in df['tweets']])
    content = str(df.head(20))
    print("Do you want to put the result into log.txt")
    jj = input()
    if (jj == 1):
        with io.open("log.txt","w",encoding="utf-8") as f:
            f.write(content)
        f.close()
    location = "nothing"
    inputname = "log.txt"
    print("Enter 1 to save the link to database, or any other number to skip saving")
    choice = input();
    if (choice == 1):
        for root, dirs, files in os.walk(r'C:\Users\Vanquish\Desktop\EC601-master'):
            for name in files:
                if name == inputname:
                    location = os.path.abspath(os.path.join(root, name))
                    print(location)
        if (location != "nothing"):
            ll = str(location)
            nn = str(inputname)
            sql = "INSERT INTO filelocation (name, address) VALUES (%s, %s)"
            val = [(nn, ll)]
            mycursor.executemany(sql,val)
            vantage.commit()
        else:
            print("no such file")
    else:
        mycursor.execute("SELECT * FROM filelocation")

        myresult = mycursor.fetchall()
        print("All data in database")
        for x in myresult:
            print(x)
        mycursor.execute("SELECT * FROM filelocation WHERE name ='log.txt'")

        myresult = mycursor.fetchall()
        print("Twitter file is located at")
        for x in myresult:
            link = x[1]
        print(link)
    line = urllib.request.pathname2url(link)
    cont = urllib.request.urlopen('file:'+line)
    for x in cont:
        print(x)

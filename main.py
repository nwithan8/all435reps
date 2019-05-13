#!/usr/bin/python

import re
import tweepy
import json
from tweepy.streaming import StreamListener
from tweepy import Stream
import twitter
import requests
from urllib3.exceptions import ProtocolError
#import gspread
#from oauth2client.service_account import ServiceAccountCredentials

#Twitter API Credentials
consumer_key = 'xxxxx'
consumer_secret = 'xxxx'
access_token = 'xxxx'
access_secret = 'xxxx'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
twitter = tweepy.API(auth)

#IFTTT Webhook URL (for app: https://ifttt.com/applets/98969598d-if-maker-event-all435reps-then-add-row-to-google-drive-spreadsheet)
URL = "https://maker.ifttt.com/trigger/all435reps/with/key/xxxx"
DATA = ""
LINK = ""
NAME = ""


USERNAMES = []
REAL_NAMES = []
USER_IDS = []

#Twitter list import
for member in tweepy.Cursor(twitter.list_members, 'TwitterGov','us-house').items():
    USER_IDS.append(str(member.id))
    REAL_NAMES.append(member.name)
    USERNAMES.append(str(member.screen_name))

print("Names and accounts imported. Now monitoring...")

def from_creator(status):
    if hasattr(status, 'retweeted_status'):
        return False
    elif status.in_reply_to_status_id != None:
        return False
    elif status.in_reply_to_screen_name != None:
        return False
    elif status.in_reply_to_user_id != None:
        return False
    else: #If not retweet and not in reply to another tweet
        return True

def retweet(status):
   twitter.retweet(status.id)

def archive(status):
    global DATA
    NAME = REAL_NAMES[USER_IDS.index(str(status.user.id))] + " (@" + USERNAMES[USER_IDS.index(str(status.user.id))] + ")"
    try:
        DATA = {'value1':NAME, 'value2':grabtext(status),'value3':"twitter.com/" + str(status.user.screen_name) + "/status/" + str(status.id)}
    except UnicodeEncodeError: #If ascii error with status text, at least archive a link to the tweet
        DATA = {'value1':NAME, 'value2':"[ERROR SAVING TEXT. PlEASE VISIT LINK.] ",'value3':"twitter.com/" + str(status.user.screen_name) + "/status/" + str(status.id)}
    requests.post(url=URL,data=DATA)

def grabtext(status):
    try:
        return status.extended_tweet["full_text"]
    except AttributeError:
        return status.text

def process_status(status):
    if from_creator(status):
            print("@" + status.user.screen_name + " tweeted: \'" + grabtext(status) + "\'")
            archive(status) #Archiving is more important, so do first
            retweet(status)

class StdOutListener(StreamListener):

    def on_status(self, status):
        process_status(status)

    def on_error(self, status_code):
        print("Error, code" + status_code)

if __name__ == '__main__':
    l = StdOutListener()
    stream = Stream(auth, l)
    while True:
        try:
            print("Connection started.")
            stream.filter(follow=USER_IDS)
        except (ProtocolError, AttributeError): #Force restart if error out
            print("Connection timed out. Restarting...")
            continue

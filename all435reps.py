#!/usr/bin/python3

import os
from typing import List, Union

import objectrest
import tweepy
from dotenv import load_dotenv

load_dotenv()

# Twitter API Credentials
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# IFTTT Webhook URL (for app: https://ifttt.com/applets/98969598d-if-maker-event-all435reps-then-add-row-to-google
# -drive-spreadsheet)
_key = os.environ.get('IFTTT_KEY')
IFTTT_WEBHOOK_URL = f"https://maker.ifttt.com/trigger/all435reps/with/key/{_key}"

# US House member list (via @TwitterGov):
LIST_ID = "63915247"  # https://twitter.com/i/lists/63915247


class HouseMemberStream(tweepy.StreamingClient):

    def __init__(self, client: tweepy.Client, bearer_token: str, house_member_twitter_accounts: List[tweepy.User]):
        super().__init__(bearer_token=bearer_token)
        self.tweeting_client: tweepy.Client = client
        self.house_member_twitter_accounts: List[tweepy.User] = house_member_twitter_accounts

    def _get_member_from_tweet(self, tweet: tweepy.Tweet) -> Union[tweepy.User, None]:
        for member in self.house_member_twitter_accounts:
            if member.id == tweet.author_id:
                return member
        return None

    def on_connect(self):
        print("Connected to Twitter API")

    def on_disconnect(self):
        print("Disconnected from Twitter API")

    def on_tweet(self, tweet: tweepy.Tweet):
        member: tweepy.User = self._get_member_from_tweet(tweet=tweet)
        if not member:
            pass
        else:
            process_status(tweet, member, self.tweeting_client)

    def on_errors(self, errors):
        print(f"Errors {errors}")

    def on_exception(self, exception):
        print(f"Exception {exception}")


def archive_tweet(tweet: tweepy.Tweet, member_name: str, member_username: str) -> None:
    data = {
        'value1': f"{member_name} (@{member_username})",
        'value2': tweet.text,
        'value3': f"twitter.com/{member_username}/status/{tweet.id}"
    }

    objectrest.post(url=IFTTT_WEBHOOK_URL, data=data)


def retweet(client: tweepy.Client, tweet: tweepy.Tweet) -> None:
    client.retweet(tweet_id=tweet.id)


def process_status(tweet: tweepy.Tweet, member: tweepy.User, tweeting_client: tweepy.Client) -> None:
    print(f"@{member.name} tweeted: \'{tweet.text}\'")

    # Archiving is more important, so do first
    archive_tweet(tweet=tweet, member_name=member.name, member_username=member.username)
    retweet(client=tweeting_client, tweet=tweet)


if __name__ == '__main__':
    # Set up Twitter client
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN,
                           consumer_key=TWITTER_CONSUMER_KEY,
                           consumer_secret=TWITTER_CONSUMER_SECRET,
                           access_token=TWITTER_ACCESS_TOKEN,
                           access_token_secret=TWITTER_ACCESS_TOKEN_SECRET)

    # Get list of all House members
    house_members_list_summary: tweepy.Response = client.get_list_members(LIST_ID)
    house_members_twitter_accounts: List[tweepy.User] = house_members_list_summary.data

    stream = HouseMemberStream(client=client,
                               bearer_token=TWITTER_BEARER_TOKEN,
                               house_member_twitter_accounts=house_members_twitter_accounts)

    from_filter = " OR ".join([f"from: {house_member.id}" for house_member in house_members_twitter_accounts])
    stream.add_rules(tweepy.StreamRule(from_filter))

    print("Names and accounts imported. Now monitoring...")

    stream.filter(tweet_fields=["id", "author_id", "text"])

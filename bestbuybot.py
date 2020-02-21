#!/usr/bin/python3

import praw
import re
import prawcore
from bestbuy.apis import BestBuy
import time
import os

bb = BestBuy(os.environ.get('BEST_BUY_API_KEY'))

mention = "u/BestBuy_Bot"

reddit = praw.Reddit(client_id=os.environ.get('BBB_CLIENT_ID'), client_secret=os.environ.get('BBB_CLIENT_SECRET'),
                     user_agent='BestBuyBot (by u/grtgbln)', username='BestBuy_Bot', password=os.environ.get('BBB_PASSWORD'))
if not reddit.read_only:
    print("Connected and running.")


def process(comment, text, rateLimitPlea=None, failedCount=0):
    if text:
        if text[0] == 'sku' and len(text) > 1:
            sku = text[1]
            api_response = bb.ProductAPI.search_by_sku(sku=sku)
        elif text[0] in ['upc', 'barcode'] and len(text) > 1:
            upc = text[1]
            api_response = bb.ProductAPI.search_by_upc(upc=upc)
        else:
            keyword = ' '.join(text)
            print(keyword)
            api_response = bb.ProductAPI.search(searchTerm=keyword)
        if api_response:
            reply = ""
            for product in api_response[:5]:
                reply += '**{name}**\n\n${price}\n\nSKU: {sku}\n\nLink: {link}\n\n'.format(name=product.name,
                                                                                    price=product.salePrice,
                                                                                    sku=product.sku,
                                                                                    link=product.url)
            reply += "\n{plea}".format(plea=(rateLimitPlea if rateLimitPlea else ""))
        else:
            reply = "I couldn't find that product, sorry."
        reply += "\n\n^(Created by u/grtgbln)"
        print(reply)
        try:
            if failedCount > 3:
                send_private_message()
            else:
                comment.reply(reply)
            comment.mark_read()
        except prawcore.exceptions.Forbidden as e:
            print("Unable to reply\nMessage:{}\nSubreddit: {}".format(comment.body, comment.subreddit.name))
        except Exception as e:
            wait_time = time_to_wait(e)
            print("Couldn't send reply. Waiting {} second(s) to try again...".format(wait_time))
            time.sleep(int(wait_time))
            process(comment=comment, text=text, rateLimitPlea="\n^(I was rate-limited while replying to you. "
                                                              "Please remember to upvote me so I don't get delayed in "
                                                              "the future.)")


def parse_message(message):
    return ' '.join([word.lower() for word in message.split() if (word != mention and word != '/' + mention)])


def time_to_wait(errorMessage):
    try:
        msg = str(errorMessage).lower()
        search = re.search(r'\b(minute[s]*)\b', msg)
        minutes = int(msg[search.start() - 2]) + 1
        return minutes * 60
    except:
        return 60


def main():
    print("Checking mentions...")
    for item in reddit.inbox.unread():
        if mention in item.body:
            text = item.body
            print(text)
            process(comment=item, text=parse_message(text).split())
    time.sleep(1)
    main()


main()

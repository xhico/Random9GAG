# -*- coding: utf-8 -*-
# !/usr/bin/python3

# python3 -m pip install tweepy selenium python-dateutil --no-cache-dir
import json
import os
import urllib.request
import tweepy
import yagmail
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service


def get911(key):
    with open('/home/pi/.911') as f:
        data = json.load(f)
    return data[key]


CONSUMER_KEY = get911('TWITTER_9GAG_CONSUMER_KEY')
CONSUMER_SECRET = get911('TWITTER_9GAG_CONSUMER_SECRET')
ACCESS_TOKEN = get911('TWITTER_9GAG_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = get911('TWITTER_9GAG_ACCESS_TOKEN_SECRET')
EMAIL_USER = get911('EMAIL_USER')
EMAIL_APPPW = get911('EMAIL_APPPW')
EMAIL_RECEIVER = get911('EMAIL_RECEIVER')

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


def getRandomPost():
    postURL, postTitle, postTags, postSrc = None, None, None, None

    # Get Random Post until src is found
    while postSrc is None or postTitle is None or postTags is None or postSrc is None:
        print("getRandomPost")
        browser.get("https://bit.ly/ShuffleNav")

        # Get Post URL and Post Title
        postURL = browser.current_url
        postTitle = browser.find_element(By.CLASS_NAME, "post-page").find_element(By.TAG_NAME, "h1").text

        # Get Post Tags
        try:
            postTags = " ".join(["#" + tag.text.replace(" ", "") for tag in browser.find_element(By.CLASS_NAME, "post-tag").find_elements(By.TAG_NAME, "a")])
        except Exception:
            postTags = ""
        postTags = ("#9GAG " + postTags).strip()

        # Check if image or video
        postMedia = browser.find_element(By.CLASS_NAME, "post-view")
        mediaClass = postMedia.get_attribute("class")
        if "gif-post" in mediaClass or "video-post" in mediaClass:
            postSrc = postMedia.find_elements(By.TAG_NAME, "source")[-1].get_attribute("src")
        elif "image-post" in mediaClass:
            postSrc = postMedia.find_element(By.TAG_NAME, "img").get_attribute("src")

    return postURL, postTitle, postTags, postSrc


def tweet(postSrc, message):
    print("Try: " + postSrc)
    try:
        tmpFile = "tmpFile." + postSrc.split(".")[-1]
        urllib.request.urlretrieve(postSrc, tmpFile)
        api.update_status(status=message, media_ids=[api.media_upload(tmpFile).media_id_string])
        print("Tweet")
        return True
    except Exception as ex:
        print(ex)
        print("Failed")
    return False


def favTweets(tags, numbTweets):
    tags = tags.replace(" ", " OR ")
    tweets = tweepy.Cursor(api.search_tweets, q=tags).items(numbTweets)
    tweets = [tw for tw in tweets]

    for tw in tweets:
        try:
            tw.favorite()
            print(str(tw.id) + " - Like")
        except Exception as e:
            print(str(tw.id) + " - " + str(e))
            pass

    return True


def main():
    checkEnd, postTags = False, ""
    while not checkEnd:
        postURL, postTitle, postTags, postSrc = getRandomPost()
        print(postURL)
        print(postTitle)
        print(postTags)

        # Tweet!
        checkEnd = tweet(postSrc, postTitle + "\n\n" + postURL + "\n\n" + postTags)
        print("----------------------------------------------------")

    # Get tweets -> Like them
    favTweets(postTags, 10)

    return


if __name__ == "__main__":
    print("----------------------------------------------------")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    headless = True
    options = Options()
    options.headless = headless
    service = Service("/home/pi/geckodriver")
    # service = Service(r"C:\Users\xhico\OneDrive\Useful\geckodriver.exe")
    browser = webdriver.Firefox(service=service, options=options)

    try:
        main()
    except Exception as ex:
        print(ex)
        yagmail.SMTP(EMAIL_USER, EMAIL_APPPW).send(EMAIL_RECEIVER, "Error - " + os.path.basename(__file__), str(ex))
    finally:
        if headless:
            browser.close()
            print("Close")
        print("End")
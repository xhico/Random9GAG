# -*- coding: utf-8 -*-
# !/usr/bin/python3

import logging
import os
import urllib.request
import tweepy
import yagmail
import psutil
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from Misc import get911


def getRandomPost():
    """
    Scrape the https://bit.ly/ShuffleNav website for a random post and return its details.

    Returns:
    (tuple): A tuple containing details of the random post scraped from the website. The tuple contains four elements:
        - postURL (str): The URL of the post.
        - postTitle (str): The title of the post.
        - postTags (str): The tags of the post, separated by spaces and with the "#9GAG" tag appended to the start.
        - postSrc (str): The source URL of the media (image or video) of the post.
    """
    postURL, postTitle, postTags, postSrc = None, None, None, None

    # Get Random Post until src is found
    while postSrc is None or postTitle is None or postTags is None or postSrc is None:
        # Log the function name
        logger.info("getRandomPost")
        # Navigate to the ShuffleNav website
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


def tweet(postSrc: str, message: str):
    """
    Downloads an image from the given URL, creates a temporary file,
    uploads the image to Twitter, and tweets the given message along
    with the uploaded image.

    Args:
        postSrc (str): The URL of the image to be tweeted.
        message (str): The message to be tweeted along with the image.

    Returns:
        bool: True if the tweet was successful, False otherwise.
    """
    try:
        # Create a temporary file for the downloaded image
        tmpFile = os.path.join(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "tmpFile." + postSrc.split(".")[-1]))

        # Download the image from the given URL
        urllib.request.urlretrieve(postSrc, tmpFile)

        # Upload the image to Twitter and get the media ID
        media_id = api.media_upload(tmpFile).media_id_string

        # Tweet the message along with the uploaded image
        api.update_status(status=message, media_ids=[media_id])

        # Log the success of the tweet
        logger.info("Tweet")

        return True
    except Exception as ex:
        # Log any errors that occur
        logger.error(ex)

    return False


def favTweets(tags: str, numbTweets: int) -> bool:
    """
    This function favorites a number of tweets containing certain tags.

    Parameters:
    tags (str): The string of tags separated by space to search for in tweets.
    numbTweets (int): The number of tweets to favorite.

    Returns:
    bool: Returns True if the tweets are successfully favorited, otherwise returns False.

    """
    logger.info("favTweets")  # logs information about the function
    tags = tags.replace(" ", " OR ")  # replaces spaces in the tags string with "OR" for search
    tweets = tweepy.Cursor(api.search_tweets, q=tags).items(numbTweets)  # searches for tweets containing the specified tags
    tweets = [tw for tw in tweets]  # adds the found tweets to a list

    for tw in tweets:  # loops through each tweet in the list
        try:
            tw.favorite()  # favorites the tweet
        except Exception as e:
            pass  # if an exception occurs while favoriting, ignores it and continues with the loop

    return True  # returns True when all tweets have been favorited


def main():
    """Main function for running the bot."""
    # Set checkEnd to False and postTags to an empty string
    checkEnd, postTags = False, ""

    # Run loop until checkEnd is True
    while not checkEnd:
        # Get a random post's URL, title, tags and source
        postURL, postTitle, postTags, postSrc = getRandomPost()

        # Log the URL of the post
        logger.info(postURL)

        # Tweet the post's source, title, URL and tags
        checkEnd = tweet(postSrc, postTitle + "\n\n" + postURL + "\n\n" + postTags)

    # Like the tweets containing postTags, up to 10 tweets
    favTweets(postTags, 10)

    # End of main function
    return


if __name__ == "__main__":
    # Set Logging
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{os.path.abspath(__file__).replace('.py', '.log')}")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
    logger = logging.getLogger()

    logger.info("----------------------------------------------------")

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

    # Check if script is already running
    procs = [proc for proc in psutil.process_iter(attrs=["cmdline"]) if os.path.basename(__file__) in '\t'.join(proc.info["cmdline"])]
    if len(procs) > 2:
        logger.info("isRunning")
    else:
        headless = True
        options = Options()
        options.headless = headless
        service = Service("/home/pi/geckodriver")
        # service = Service(r"C:\Users\xhico\OneDrive\Useful\geckodriver.exe")
        browser = webdriver.Firefox(service=service, options=options)

        try:
            main()
        except Exception as ex:
            logger.error(traceback.format_exc())
            yagmail.SMTP(EMAIL_USER, EMAIL_APPPW).send(EMAIL_RECEIVER, "Error - " + os.path.basename(__file__), str(traceback.format_exc()))
        finally:
            if headless:
                browser.close()
                logger.info("Close")
            logger.info("End")

import pytumblr
from threading import Thread
import requests
import logging
import json
from boto.s3.connection import S3Connection
import time
import sys

class Scrape():

    def __init__(self, aws_access_key, aws_secret_key, s3_bucket, tumblr_api_key, tag, refresh_period=1.0):

        self.tumblr_client = pytumblr.TumblrRestClient(tumblr_api_key)

        s3_client = S3Connection(aws_access_key, aws_secret_key)
        self.bucket = s3_client.get_bucket(s3_bucket)

        # List the files in our bucket, find jsons and remove them, leaving the id, then setify it. That way we don't
        # download the same file twice
        self.scraped_ids = set([filename.key[:-5] for filename in self.bucket.get_all_keys() if filename.key[-5:]=='.json'])

        self.tag = tag
        self.refresh_period = refresh_period
        self.scraping = False

    def input_thread(self):
        raw_input("")
        self.scraping = False

    def start(self):
        logging.info("Starting scrape.")
        self.scraping = True

        i = 1

        interrupt_thread = Thread(target=self.input_thread)
        interrupt_thread.start()

        while self.scraping:
            loader = {0: '|', 1: '/', 2: '-', 3: '\\'}

            sys.stdout.write('\r')
            sys.stdout.flush()
            sys.stdout.write("Scrape #" + str(i) + " " + loader[i % 4] + "    Press any key to stop")

            # Spin off a thread to get the posts. This doesn't technically need to be in a thread, but I wanted
            # to future proof it in case I want to get multiple tags concurrently.
            t = Thread(target=self.post_thread)
            t.start()
            t.join()
            time.sleep(self.refresh_period)
            i += 1

    def stop(self):
        sys.stdout.flush()
        self.scraping = False

    def post_thread(self):
        response = self.tumblr_client.tagged(self.tag)
        content_list = self.parse_content_urls(response)

        image_threads = []

        # Loop through the posts that got returned, then spin off threads to download the images associated with them.
        for content in content_list:
            image_threads.append(Thread(target=self.upload_content, args=(content,)))
            image_threads[-1].start()

        # Wait for all the images to download before we close the post thread.
        for image_thread in image_threads:
            image_thread.join()

    def upload_content(self, content):
        id = str(content[0])
        post = content[1]

        if id in self.scraped_ids:
            return

        if content[2] is not None:
            img_url = content[2]
            img_filename = img_url.split('/')[-1]

            # We put the image in a directory with the post id in the directory name
            image_key = self.bucket.new_key(id+'/'+img_filename)
            r = requests.get(img_url)

            if r.status_code == 200:
                json_key = self.bucket.new_key(id + '.json')
                json_key.set_contents_from_string(json.dumps(post))

                image_key.content_type = r.headers['content-type']
                image_key.set_contents_from_string(r.content)

        else:
            json_key = self.bucket.new_key(id + '.json')
            json_key.set_contents_from_string(json.dumps(post))

    def parse_content_urls(self, posts):
        content = []

        # If the post doesn't have one and only one photo in it, we will still save the json (for later), but won't
        # download any photos.
        for post in posts:
            id = post['id']

            if post['type'] == 'photo' and len(post['photos']) == 1:
                img_url=post['photos'][0]['original_size']['url']
                content.append((id, post, img_url))
            else:
                content.append((id, post, None))

        return content
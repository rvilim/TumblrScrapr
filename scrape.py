import pytumblr
from threading import Thread
import requests
import logging
import json
from boto.s3.connection import S3Connection
import time
import sys
from Queue import Queue

class Scrape():

    def __init__(self, aws_access_key, aws_secret_key, s3_bucket, tumblr_api_key, tag, mean_time=1.0):

        self.tumblr_client = pytumblr.TumblrRestClient(tumblr_api_key)

        s3_client = S3Connection(aws_access_key, aws_secret_key)
        self.bucket = s3_client.get_bucket(s3_bucket)

        self.scraped_ids = set([filename.key[:-5] for filename in self.bucket.get_all_keys() if filename.key[-5:]=='.json'])

        self.tag = tag
        self.mean_time = mean_time

    def input_thread(self):
        raw_input("Press any key to stop")
        self.scraping = False

    def start(self):
        logging.info("Starting scrape.")
        self.scraping = True


        i = 1

        q=Queue()
        interrupt_thread = Thread(target=self.input_thread)
        interrupt_thread.start()

        while self.scraping:
            loader = {0: '|', 1: '/', 2: '-', 3: '\\'}

            sys.stdout.write('\r')
            sys.stdout.flush()
            sys.stdout.write("Scrape #" + str(i) + " " + loader[i % 4] + "    Press any key to stop")

            t=Thread(target=self.get_posts)
            t.start()
            t.join()
            time.sleep(1.0)
            i+=1

    def stop(self):
        sys.stdout.flush()
        self.scraping = False

    def get_posts(self):
        postthread=Thread(target=self.post_thread)
        postthread.start()
        postthread.join()

    def post_thread(self):
        response = self.tumblr_client.tagged(self.tag)
        content_list = self.parse_content_urls(response)

        threads=[]

        for content in content_list:
            threads.append(Thread(target=self.upload_content, args=(content,)))
            threads[-1].start()

        for thread in threads:
            thread.join()

    def upload_content(self, content):
        id = str(content[0])
        post = content[1]

        if id in self.scraped_ids:
            return

        if content[2] is not None:
            img_url = content[2]
            img_filename = img_url.split('/')[-1]

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

        for post in posts:
            id = post['id']

            if post['type'] == 'photo' and len(post['photos']) == 1:
                img_url=post['photos'][0]['original_size']['url']
                content.append((id, post, img_url))
            else:
                content.append((id, post, None))

        return content
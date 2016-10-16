import pytumblr

class Scrape():

    def __init__(self, api_key, tags):
        self.api_key = api_key
        self.client = pytumblr.TumblrRestClient(api_key)
        self.tags = tags

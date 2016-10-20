import config
import scrape


def main():

    CONFIG = config.init_config('application.ini')

    aws_access_key = CONFIG.get('aws', 'AWS_ACCESS_KEY')
    aws_secret_key = CONFIG.get('aws', 'AWS_SECRET_KEY')
    s3_bucket = CONFIG.get('aws', 'S3_BUCKET')

    tumblr_api_key = CONFIG.get('tumblr', 'API_KEY')
    refresh_period = CONFIG.getfloat('tumblr', 'REFRESH_PERIOD')
    tags = 'instagram'

    scraper = scrape.Scrape(aws_access_key, aws_secret_key, s3_bucket, tumblr_api_key, tags, refresh_period=refresh_period)
    scraper.start()

if __name__ == '__main__':
    main()
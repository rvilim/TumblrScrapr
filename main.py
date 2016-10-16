import config
import scrape


def main():
    CONFIG = config
    CONFIG.init_config('application.ini')

if __name__ == '__main__':
    main()
import logging
import ConfigParser
import sys


def init_config(file='application.ini'):
    config = ConfigParser.SafeConfigParser()
    config.read(file)

    try:

        config.read(file)
    except ConfigParser.Error as error:
        logging.critical("Error {error}: Error reading config file {file}.".format(error=error, file=file))
        sys.exit(1)
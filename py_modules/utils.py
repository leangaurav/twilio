import logging
import sys

def get_logger():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    return logging.getLogger()

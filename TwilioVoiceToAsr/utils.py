import logging
import sys

def get_logger():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    return logging.getLogger()

def set_google_creds_path(path: str):
    import os
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path

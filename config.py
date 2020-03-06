import logging
import os

TOKEN = os.environ['BOT_TOKEN']
PING_INTERVAL = 300


def set_default_logging_config():
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=logging.DEBUG
    )

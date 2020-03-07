import logging
import os

TOKEN = os.environ['BOT_TOKEN']
DATABASE_HOST = os.environ['POSTGRES_HOST']
DATABASE_NAME = os.environ['POSTGRES_DB']
DATABASE_USERNAME = os.environ['POSTGRES_USER']
DATABASE_PASSWORD = os.environ['POSTGRES_PASSWORD']
REDIS_HOST = os.environ['REDIS_HOST']
PING_INTERVAL = 300


def set_default_logging_config():
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=logging.DEBUG
    )


def database_uri():
    return f'postgres://{DATABASE_USERNAME}:{DATABASE_PASSWORD}\
@{DATABASE_HOST}/{DATABASE_NAME}'

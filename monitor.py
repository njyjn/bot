import aioredis
import asyncio
import redis
import signal
import sys
from app import _send_message
from config import logging, set_default_logging_config
from exception import shutdown, handle_exception


async def init():
    print("Welcome to Message Monitor")
    set_default_logging_config()
    r, channel, msg = await redis.subscribe()
    return r, channel, msg


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(loop, s))
        )
    loop.set_exception_handler(handle_exception)

    r, ch1, msg = loop.run_until_complete(init())
    logging.info(msg)

    try:
        loop.create_task(redis.read(ch1))
        loop.run_forever()
    finally:
        logging.info(loop.run_until_complete(redis.unsubscribe(r)))
        loop.close()
        logging.info("Successfully shutdown the Monitor")

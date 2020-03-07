import aioredis
import asyncio
import redis
import signal
import sys
from app import _send_message
from client import create_client_session
from config import logging, set_default_logging_config
from exception import shutdown, handle_exception


async def _send_message_from_cli(id, message, client_session):
    try:
        response = await _send_message(id, message, client_session)
        if response['ok'] is False:
            raise Exception(response['description'])
        print('>>> Sent "%s" to %s' % (message, id))
    except Exception as e:
        print('>>> Failed to send message: "%s"' % (e))
        raise


async def run(client_session):
    print("Welcome to Message Transmitter\n\n:: \
        Use :c to change id anytime\n")
    try:
        while True:
            id = await read_id()
            while True:
                message = await read_message()
                if message == ':c':
                    break
                try:
                    await _send_message_from_cli(
                        id, message, client_session)
                except Exception:
                    break
    except (KeyboardInterrupt, EOFError):
        print("\n\nGoodbye. HAND")
        await client_session.close()
        SystemExit()


async def read_id():
    return input("Enter id: ")


async def read_message():
    return input("Enter message: ")


async def main():
    try:
        client_session = await create_client_session()
        await run(client_session)
    except Exception:
        print(sys.exc_info())
        await client_session.close()
        SystemError()


if __name__ == '__main__':
    set_default_logging_config()
    asyncio.run(main())

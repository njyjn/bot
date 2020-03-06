import aiohttp
import asyncio
import json
import uvloop
from config import logging, set_default_logging_config


def init_client():
    set_default_logging_config()


async def create_client_session():
    return aiohttp.ClientSession()


async def post(url, body=None, session=None):
    after_close = False
    if not session:
        session = create_client_session()
        after_close = True
    async with session.post(url, data=body) as resp:
        response = await resp.json()
    if after_close:
        await session.close()
    return response


async def get(url, params=None, session=None):
    after_close = False
    if not session:
        session = create_client_session()
        after_close = True
    async with session.get(url, params=params) as resp:
        response = await resp.json()
    if after_close:
        await session.close()
    return response

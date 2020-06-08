import aiohttp_jinja2
import asyncio
import json
import sys
from aiohttp import web
from client import start_client, post, get
from config import logging, TOKEN, set_default_logging_config, PING_INTERVAL
from exception import shutdown, handle_exception
from jinja2 import FileSystemLoader
from models.user import User
from redis import publish, close, send
from responder import process_input
from telegram import assemble_uri
from views import view_routes, VIEWS_URL_PREFIX
from api_v1 import api_routes, API_URL_PREFIX


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status == 200 or response.status == 302 or response.status == 401:
            return response
        message = response.message
        status_code = response.status
    except web.HTTPException as ex:
        if ex.status == 200 or ex.status == 302 or ex.status == 401:
            raise
        message = ex.reason
        status_code = ex.status
    return web.json_response({
        'status_code': status_code,
        'error': message
    }, status=status_code)


async def init_db(app):
    # Initiate Postgres Engine for database tasks
    app['db'] = await User.start_engine()
    logging.info('Database engine started')


async def stop_db(app):
    # Initiate Postgres Engine for database tasks
    await app['db'].close()
    logging.info('Database engine stopped')


async def init_redis(app):
    # Initiate pubsub redis server connection pool
    publisher, msg = await publish()
    app['publisher'] = publisher
    await send(publisher, "Server started. You made it")
    logging.info(msg)


async def stop_redis(app):
    # Stop pubsub redis server connection pool
    publisher = app['publisher']
    await send(publisher, f"Godspeed!")
    msg = await close(publisher)
    logging.info(msg)


async def init_client(app):
    # Initiate client for outbound requests
    app['client_session'] = await start_client()
    logging.info('Client session created')


async def stop_client(app):
    # Stop client for outbound requests
    app['client_session'].close()
    await app['client_session'].wait_closed()
    logging.info('Client session stopped')


async def init_background(app):
    # Start all background tasks
    await start_background_tasks(app)


async def stop_background(app):
    # Stop all background tasks
    await stop_background_tasks(app)


async def stop_app(app):
    loop = asyncio.get_event_loop()
    await shutdown(loop)


async def ping(app):
    while True:
        await send(
            app['publisher'],
            f"Stay strong... See you in {PING_INTERVAL}"
        )
        logging.info("Ping sent to subscribers")
        await asyncio.sleep(PING_INTERVAL)


async def start_background_tasks(app):
    app['ping'] = asyncio.create_task(ping(app))


async def stop_background_tasks(app):
    app['ping'].cancel()
    await app['ping']


async def create_app():
    app = web.Application(middlewares=[
        error_middleware,
        bauth
    ])

    app.on_shutdown.append(stop_app)

    api_v1 = web.Application()
    api_v1.add_routes(api_routes)
    api_v1.on_startup.append(init_redis)
    api_v1.on_startup.append(init_client)
    api_v1.on_startup.append(init_db)
    api_v1.on_startup.append(init_background)
    api_v1.on_cleanup.append(stop_redis)
    api_v1.on_cleanup.append(stop_client)
    api_v1.on_cleanup.append(stop_db)
    api_v1.on_cleanup.append(stop_background)
    app.add_subapp(API_URL_PREFIX, api_v1)

    views = web.Application()
    views.add_routes(view_routes)
    aiohttp_jinja2.setup(views, loader=FileSystemLoader('./templates'))
    views.on_startup.append(init_client)
    views.on_startup.append(init_db)
    views.on_cleanup.append(stop_client)
    views.on_cleanup.append(stop_db)
    app.add_subapp(VIEWS_URL_PREFIX, views)

    set_default_logging_config()

    return app


if __name__ == '__main__':
    web.run_app(create_app())

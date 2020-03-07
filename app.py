import aiohttp_jinja2
import asyncio
import json
import sys
from aiohttp import web
from client import start_client, post, get
from config import logging, TOKEN, set_default_logging_config, PING_INTERVAL
from exception import shutdown, handle_exception
from jinja2 import FileSystemLoader
from models import Database
from redis import publish, close, send
from responder import process_input
from telegram import assemble_uri
from views import view_routes, VIEWS_URL_PREFIX

routes = web.RouteTableDef()


@routes.post('/api/v1/bots/updates/{token}')
async def receive_from_webhook(request):
    if request.match_info['token'] != TOKEN:
        raise web.HTTPUnauthorized()
    payload = await request.json()
    params = request.query

    # Log message in pubsub queue
    username = payload['message']['from']['username']
    id = payload['message']['from']['id']
    message = (
        payload['message'].get('text') or
        payload['message'].get('sticker')['emoji']
    )
    pool = request.app['publisher']
    await send(pool, f"{username} ({id}): {message}")

    # Process message
    db = request.app['db']
    will_reply = await process_input(db, payload, params)
    if will_reply:
        client_session = request.app['client_session']
        await _send_message(id, will_reply, client_session)

    response = {
        'you_are': payload['message']['from']
    }
    return web.json_response(
        response,
        content_type='application/json'
    )


@routes.get('/api/v1/bots/webhooks')
async def get_webhook(request):
    try:
        client_session = request.app['client_session']
        response = await get(
            assemble_uri(TOKEN, 'getWebhookInfo'),
            session=client_session
        )
        return web.json_response(
            response,
            content_type='application/json'
        )
    except Exception:
        print(sys.exc_info())
        raise web.HTTPUnprocessableEntity()


@routes.post('/api/v1/bots/webhooks')
async def set_webhook(request):
    try:
        payload = await request.json()
        url = payload['url']
        allowed_updates = payload['allowed_updates']
        client_session = request.app['client_session']
        response = await get(
            assemble_uri(TOKEN, 'setWebhook'),
            {
                'url': url,
                'allowed_updates': json.dumps(allowed_updates)
            },
            client_session
        )
        return web.json_response(
            response,
            content_type='application/json'
        )
    except Exception:
        print(sys.exc_info())
        raise web.HTTPUnprocessableEntity()


@routes.post('/api/v1/bots/messages')
async def send_message(request):
    try:
        payload = await request.json()
        chat_id = payload['chat_id']
        message = payload['message']
        client_session = request.app['client_session']
        response = await _send_message(chat_id, message, client_session)
        return web.json_response(
            response,
            content_type='application/json'
        )
    except Exception:
        print(sys.exc_info())
        raise web.HTTPUnprocessableEntity()


async def _send_message(chat_id, message, client_session=None):
    response = await get(
        assemble_uri(TOKEN, 'sendMessage'),
        {
            'chat_id': chat_id,
            'text': message
        },
        client_session
    )
    return response


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status == 200:
            return response
        message = response.message
        status_code = response.status_code
    except web.HTTPException as ex:
        if ex.status == 200:
            raise
        message = ex.reason
        status_code = ex.status
    return web.json_response({
        'status_code': status_code,
        'error': message
    }, status=status_code)


async def init_db(app):
    # Initiate Postgres Engine for database tasks
    app['db'] = await Database.start_engine()
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
    await app['client_session'].close()
    logging.info('Client session stopped')


async def init_background(app):
    # Start all background tasks
    await start_background_tasks(app)


async def stop_background(app):
    # Stop all background tasks
    await stop_background_tasks(app)


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
    app = web.Application(middlewares=[error_middleware])

    app.add_routes(routes)
    app.on_startup.append(init_redis)
    app.on_startup.append(init_client)
    app.on_startup.append(init_db)
    app.on_cleanup.append(stop_redis)
    app.on_cleanup.append(stop_client)
    app.on_cleanup.append(stop_db)
    app.on_cleanup.append(stop_background)

    views = web.Application()
    views.add_routes(view_routes)
    aiohttp_jinja2.setup(views, loader=FileSystemLoader('./templates'))
    views.on_startup.append(init_client)
    views.on_startup.append(init_db)
    views.on_cleanup.append(stop_client)
    app.add_subapp(VIEWS_URL_PREFIX, views)

    set_default_logging_config()

    return app


if __name__ == '__main__':
    web.run_app(create_app())

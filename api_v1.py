import asyncio
import json
import sys
from aiohttp import web
from client import post, get
from config import logging, TOKEN, HOST_PREFIX
from exception import shutdown, handle_exception
from models.user import User
from redis import publish, close, send
from responder import process_input
from telegram import assemble_uri


API_URL_PREFIX = HOST_PREFIX + '/api/v1'

api_routes = web.RouteTableDef()


@api_routes.post('/bots/updates/{token}')
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
        payload['message'].get('sticker', {}).get('emoji')
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


@api_routes.get('/bots/webhooks')
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


@api_routes.post('/bots/webhooks')
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


@api_routes.post('/bots/messages')
async def send_message(request):
    try:
        payload = await request.json()
        id = payload['id']
        message = payload['message']
        client_session = request.app['client_session']
        response = await _send_message(id, message, client_session)
        return web.json_response(
            response,
            content_type='application/json'
        )
    except Exception:
        print(sys.exc_info())
        raise web.HTTPUnprocessableEntity()


async def _send_message(id, message, client_session=None):
    response = await get(
        assemble_uri(TOKEN, 'sendMessage'),
        {
            'chat_id': id,
            'text': message
        },
        client_session
    )
    return response


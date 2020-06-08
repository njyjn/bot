import aiohttp_jinja2
import json
from aiohttp import web
from auth import bauth
from client import post, get
from config import TOKEN, HOST_PREFIX
from models.user import User
from telegram import assemble_uri, assemble_webhook_uri

VIEWS_URL_PREFIX = HOST_PREFIX + '/admin'

view_routes = web.RouteTableDef()


@view_routes.get('')
async def hello(request):
    return web.Response(text="Hello World")


@view_routes.get('/users')
@aiohttp_jinja2.template('users.html')
async def get_registered_users(request):
    db = request.app['db']
    users = await db.get_all()
    response = {
        'count': len(users),
        'users': users
    }
    return response


@view_routes.get('/webhooks', name='get_webhooks')
@aiohttp_jinja2.template('forms/webhooks.html')
async def get_webhooks(request):
    client_session = request.app['client_session']
    client_response = await get(
        assemble_uri(TOKEN, 'getWebhookInfo'),
        session=client_session
    )
    response = {
        'current_webhook': client_response['result']['url'],
        'url_prefix': VIEWS_URL_PREFIX
    }
    return response


@view_routes.post('/webhooks')
async def post_webhooks(request):
    data = await request.post()
    new_webhook = assemble_webhook_uri(data['webhook'], TOKEN)
    client_session = request.app['client_session']
    client_response = await get(
        assemble_uri(TOKEN, 'setWebhook'),
        {
            'url': new_webhook,
            'allowed_updates': json.dumps(['message'])
        },
        client_session
    )
    location = request.app.router['get_webhooks'].url_for()
    raise web.HTTPFound(location=location)
    return {}

from aiohttp import web

view_routes = web.RouteTableDef()


@view_routes.get('')
async def hello(request):
    return web.Response(text="Hello World")


@view_routes.get('/{name}')
async def return_name(request):
    response = {
        'name': request.match_info['name']
    }
    return web.json_response(
        response,
        status=200,
        content_type='application/json'
    )


@view_routes.get('/users')
async def get_registered_users(request):
    response = {
        'name': request.match_info['name']
    }
    return web.json_response(
        response,
        status=200,
        content_type='application/json'
    )

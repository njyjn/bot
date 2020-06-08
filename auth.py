from aiohttp_basicauth import BasicAuthMiddleware
from config import BAUTH_USERNAME, BAUTH_PASSWORD

bauth = BasicAuthMiddleware(username=BAUTH_USERNAME, password=BAUTH_PASSWORD, force=False)


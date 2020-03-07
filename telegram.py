BASE_URI = 'https://api.telegram.org/bot'


def assemble_uri(token, method_name):
    return BASE_URI + token + '/' + method_name


def assemble_webhook_uri(base_uri, token):
    return base_uri + '/api/v1/bots/updates/' + token

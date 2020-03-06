BASE_URI = 'https://api.telegram.org/bot'


def assemble_uri(token, method_name):
    return BASE_URI + token + '/' + method_name

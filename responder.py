from config import logging, set_default_logging_config


class Responder():
    @classmethod
    async def init(cls, db, payload):
        self = Responder()
        self.db = db
        self.text = payload['message'].get('text')
        self.user = payload['message']['from']
        self.is_invited = await self.db.validate_user(self.user['id'], 'user')
        self.is_admin = await self.db.validate_user(self.user['id'], 'admin')
        return self

    async def handle_start(self):
        # Check if user is already registered
        if self.is_invited:
            return 'You are already registered with me. \
Use /stop to deregister'

        # Check deeplinked start param for invite key
        invite_key = self.text[len('/start '):]
        if not invite_key:
            return 'Sorry, you must have a valid invite code to interact'

        # TODO: Call main app to validate invite key
        # For now a static invite key
        if invite_key != 'alethea':
            return 'Invalid invite code'

        # Register user
        username = self.user['username']
        id = self.user['id']
        try:
            await self.db.register_user(
                first_name=self.user.get('first_name', '-'),
                last_name=self.user.get('last_name', '-'),
                username=username,
                id=id,
                role='user'
            )
            logging.info(f'{id} has registered')
        except Exception as e:
            logging.error(e)
            return 'Failed to register you. Try again.'
        return f'Welcome, {username}'

    async def handle_stop(self):
        id = self.user['id']
        try:
            await self.db.deregister_user(
                id
            )
            logging.info(f'{id} has deregistered')
        except Exception as e:
            logging.error(e)
        return 'Goodbye'


async def process_input(db, payload, params=[]):
    responder = await Responder.init(db, payload)
    # Customize your responses here

    # Process text messages
    if responder.text:
        if responder.text.startswith('/start'):
            return await responder.handle_start()
        if responder.text == '/stop' and responder.is_invited:
            return await responder.handle_stop()
        if responder.text.startswith('echo ') and responder.is_invited:
            return responder.text[len('echo '):]

    # Process stickers
    # TODO: Encapsulate in Responder class
    sticker = payload['message'].get('sticker')
    if sticker and responder.is_invited:
        return 'Sorry, I can\'t understand stickers yet.'
    if not responder.is_invited:
        return 'Sorry, you need to be invited to interact'
    return 'Sorry, I\'m not sure I understand'

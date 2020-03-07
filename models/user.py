import asyncio
import sqlalchemy as sa
from aiopg.sa import create_engine
from config import (DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST,
                    DATABASE_NAME, database_uri)
from sqlalchemy.sql import select, delete
from sqlalchemy_utils import database_exists, create_database

metadata = sa.MetaData()

users = sa.Table(
    'users',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String(255)),
    sa.Column('username', sa.String(255)),
    sa.Column('chat_id', sa.Integer),
    sa.Column('role', sa.String(255))
)


class User:
    @classmethod
    async def start_engine(cls):
        if not database_exists(database_uri()):
            create_database(database_uri())
        self = User()
        self.engine = await create_engine(
            user=DATABASE_USERNAME,
            database=DATABASE_NAME,
            host=DATABASE_HOST,
            password=DATABASE_PASSWORD
        )
        await _create_table(self.engine)
        return self

    async def insert(self, **kwargs):
        async with self.engine.acquire() as conn:
            await conn.execute(users.insert().values(kwargs))

    async def delete(self, id):
        async with self.engine.acquire() as conn:
            await conn.execute(
                users.delete().where(users.c.id == id)
            )

    async def get(self, id):
        async with self.engine.acquire() as conn:
            return await (await conn.execute(
                select([users]).where(users.c.id == id)
            )).fetchone()

    async def get_all(self):
        async with self.engine.acquire() as conn:
            return await (await conn.execute(
                select([users])
            )).fetchall()

    """
    User helper methods
    """
    async def register_user(self, first_name, last_name, username, id, role):
        full_name = f'{first_name} {last_name}'
        await self.insert(
                name=full_name,
                username=username,
                id=id,
                role=role
            )

    async def deregister_user(self, id):
        await self.delete(
                id=id
            )

    async def validate_user(self, id, role=None):
        user = await self.get(
                id=id,
            )
        if not user:
            return False
        if role:
            return user.role == role
        return True


async def _create_table(engine):
    async with engine.acquire() as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id serial PRIMARY KEY,
            name varchar(255),
            username varchar(255),
            chat_id integer,
            role varchar(255))''')


def firstrun():
    engine = sa.create_engine(database_uri())
    if not database_exists(engine.url):
        create_database(engine.url)


if __name__ == '__main__':
    firstrun()

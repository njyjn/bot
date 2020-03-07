import aioredis
from datetime import datetime

CHAN = 'channel:1'


async def subscribe():
    redis = await aioredis.create_redis_pool('redis://localhost')
    msg = "Successfully created redis connection pool for subscriber"
    res = await redis.subscribe(CHAN)
    ch1 = res[0]
    assert isinstance(ch1, aioredis.Channel)
    return redis, ch1, msg


async def publish():
    redis = await aioredis.create_redis_pool('redis://localhost')
    msg = "Successfully created redis connection pool for publisher"
    return redis, msg


async def read(channel):
    while True:
        message = await channel.get(encoding='utf-8')
        ts = str(datetime.now())
        print(f"[{ts}] {message}")


async def send(redis, message):
    await redis.publish(CHAN, message)


async def unsubscribe(redis):
    await redis.unsubscribe(CHAN)
    redis.close()
    await redis.wait_closed()
    return "Successfully closed redis connection pool for subscriber"


async def close(redis):
    redis.close()
    await redis.wait_closed()
    return "Successfully closed redis connection pool for publisher"

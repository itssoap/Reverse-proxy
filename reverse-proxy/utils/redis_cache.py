"""
References: 
	https://stackoverflow.com/q/50211546/14940695
	https://stackoverflow.com/q/67413075/14940695

RedisDB is taken from:
	https://github.com/sanjit-sinha/TelegramBot-Boilerplate

I am rewriting it to cache the HTMLresponse of various pages

"""

from fastapi.responses import HTMLResponse
import pickle
from aioredis import Redis


class RedisCache:
    @classmethod
    async def set(
        cls,
        redis: Redis,
        key: str,
        value: HTMLResponse,
        ttl: int | None = None,
        ignore_if_exists: bool = True,
    ) -> bool:
        """
        Set the value at ``key`` to ``value``
        Returns 'True' if the operation is successful.

        ``ttl`` Time-to-live for a key, in ``int`` seconds.

        ``ignore_if_exists`` if True, it will ignore setting the key.
                        Set it to False to overwrite existing key-value
        """

        value_enc = await cls.encoder(value)

        if ttl is None:
            result = await redis.set(key, value_enc, nx=ignore_if_exists)

        else:
            result = await redis.set(key, value_enc, ex=ttl, nx=ignore_if_exists)

        return result

    @classmethod
    async def get(cls, redis: Redis, key: str) -> HTMLResponse:
        """
        Returns the ``value`` of provided ``key``.
        """

        value = await redis.get(key)
        # print(value)
        if value is not None:
            value = await cls.decoder(value)

        return value

    @staticmethod
    async def delete(redis: Redis, key: str) -> bool:
        """
        Deletes ``key``:``value`` pair from database, based on the ``key`` provided.
        Returns 'True' if the operation is successful.
        """

        value = await redis.delete(key)
        return bool(value)

    @staticmethod
    async def encoder(html: HTMLResponse) -> str:
        """
        Converts an ``HTMLResponse`` object to ``str`` of hex data.
        """
        return pickle.dumps(html, pickle.HIGHEST_PROTOCOL).hex()

    @staticmethod
    async def decoder(val: str) -> HTMLResponse:
        """
        Converts hex data in ``val`` to the original ``HTMLResponse`` object.
        """
        return pickle.loads(bytes.fromhex(val))

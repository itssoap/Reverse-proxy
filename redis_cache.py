"""
Reference: https://stackoverflow.com/questions/50211546/converting-byte-to-string-and-back-properly-in-python3
           https://stackoverflow.com/questions/67413075/store-instance-of-class-in-string

RedisDB is taken from https://github.com/sanjit-sinha/TelegramBot-Boilerplate

I am rewriting it to cache the HTMLresponse of various pages

"""

import aioredis
import asyncio
from fastapi.responses import HTMLResponse
import pickle
from dotenv import load_dotenv
import os

load_dotenv()
redis = aioredis.from_url(os.getenv("REDIS_URL"), decode_responses=True)


class RedisCache:

	@staticmethod
	async def set(key: str, value: str, ttl: int | None = None, ignore_if_exists: bool = True) -> bool:
		"""
		Set the value at ``key`` to ``value``
		Returns 'True' if the operation is successful.
		
		``ttl`` Time-to-live for a key, in ``int`` seconds 

		``ignore_if_exists`` if True, it will ignore setting the key.
				Set it to False to overwrite existing key-value
		"""

		if ttl is None:
			result = await redis.set(key, value, nx=ignore_if_exists)

		else:
			result = await redis.set(key, value, ex=ttl, nx=ignore_if_exists)
		return result


	@staticmethod
	async def get(key: str) -> str:
		"""
		Returns the ``value`` of provided ``key``.   
		"""

		value = await redis.get(key)
		return value


	@staticmethod
	async def delete(key: str) -> bool:
		"""
		Deletes ``key``:``value`` pair from database, based on the ``key`` provided.
		Returns 'True' if the operation is successful.
		"""

		value = await redis.delete(key) 
		return False if value == 0 else True


	@staticmethod
	async def encoder(html: HTMLResponse) -> str:
		"""
		Converts an ``HTMLResponse`` object to ``str`` of hex data.
		"""
		return pickle.dumps(html).hex()


	@staticmethod
	async def decoder(val: str) -> HTMLResponse:
		"""
		Converts hex data in ``val`` to the original ``HTMLResponse`` object.
		"""
		return pickle.loads(bytes.fromhex(val))
    

async def main():
	redis_l = RedisCache()

	with open('response_test.txt') as f:
		help_page = [line for line in f]
	print(len(help_page))

	obj = HTMLResponse(content=help_page[0], status_code=200)
	enc_obj = await redis_l.encoder(obj)

	await redis_l.set("help", enc_obj, ttl=86400, ignore_if_exists=False)

	val = await redis_l.get("help")

	dec_obj = await redis_l.decoder(str(val))
	print(dec_obj)


if __name__ == '__main__':
    asyncio.run(main())

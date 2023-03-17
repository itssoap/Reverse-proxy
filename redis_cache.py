"""
Reference: https://stackoverflow.com/questions/50211546/converting-byte-to-string-and-back-properly-in-python3
           https://stackoverflow.com/questions/67413075/store-instance-of-class-in-string

RedisDB is taken from https://github.com/sanjit-sinha/TelegramBot-Boilerplate

I am rewriting it to cache the HTMLresponse of various pages

"""

import aioredis
from typing import List, Any 
import asyncio
from fastapi.responses import HTMLResponse
import pickle
from dotenv import load_dotenv
import os

load_dotenv()
redis = aioredis.from_url(os.getenv("REDIS_URL"), decode_responses=True)


class RedisDB:

	@staticmethod
	async def set(key: str, value: str, ttl: int | None = None, ignore_if_exists: bool = True) -> bool:
		"""
		Getting and setting data in redis. It take key and value pair argument as string. 
		return 'True' if the operation is successful.
		"""

		if ttl is None:
			result = await redis.set(key, value, nx=ignore_if_exists)

		else:
			result = await redis.set(key, value, ex=ttl, nx=ignore_if_exists)
		return result


	@staticmethod
	async def get(key: str) -> str:
		"""
		Take key as argument and return string value.
		(It won't return value if that key don't store string class values.)	   
		"""

		value = await redis.get(key)
		return value


	@staticmethod
	async def delete(key: str ) -> bool:
		"""
		Take key as argument and delete the value from database.
		(It can delete any type of key, value pair including  list, set, hash )
		return 'True' if the operation is successful.
		"""

		value = await redis.delete(key) 
		return False if value == 0 else True


async def encoder(html: HTMLResponse) -> str:
    return pickle.dumps(html).hex()

async def decoder(val: str) -> HTMLResponse:
    return pickle.loads(bytes.fromhex(val))
    

async def main():
	redis_l = RedisDB()

	with open('response_test.txt') as f:
		help_page = [line for line in f]
	print(len(help_page))

	obj = HTMLResponse(content=help_page[0], status_code=200)
	enc_obj = await encoder(obj)

	await redis_l.set("help", enc_obj, ttl=86400, ignore_if_exists=False)

	val = await redis_l.get("help")

	dec_obj = await decoder(str(val))
	print(dec_obj)


if __name__ == '__main__':
    asyncio.run(main())

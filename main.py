from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
import httpx
import os
from aioredis import Redis, from_url
from redis_cache import RedisCache
from uvicorn import run

headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': 'https://nyaa.si/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Access-Control-Allow-Origin': 'http://127.0.0.1:8000'
    }


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# load_dotenv()
redis_cache = RedisCache()
redis = Redis()

@app.on_event("startup")
def startup():
    load_dotenv()
    global redis_cache, redis 
    redis_cache = RedisCache()

    print(os.getenv("REDIS_URL"))
    redis = from_url(os.getenv("REDIS_URL"), decode_responses=True)


@app.get("/", response_model=None, response_class=Response)
async def getter(request: Request) -> Response:
    resp = ""
    params = request.query_params
    print(params, flush=True)
    try:
        if params is not None:
            resp = httpx.get(f"https://nyaa.si/?{params}", headers=headers)

        else:
            resp = httpx.get(f"https://nyaa.si/", headers=headers)

    except Exception:
        pass

    flag = 0

    try:
        temp = params["page"]
    except KeyError:
        flag = 1
        
    # returning a Respone class with media_type HTML to avoid using Union of HTMLResponse and Response
    # The Union breaks the endpoint /docs, as it tries to look up media_type json for openapi.json

    return Response(content=resp.text, status_code=200, media_type="text/html") \
            if flag == 1 else Response(content=resp.text, media_type="application/xml")


@app.get("/view/{view_id}", response_class=HTMLResponse)
async def getter(view_id: int | None = None) -> HTMLResponse:
    # page:str | None = None
    resp = ""
    try:
        # if page is not None:
            # resp = httpx.get(f"https://nyaa.si/view/{view_id}?page={page}", headers=headers)
        # else:
        resp = httpx.get(f"https://nyaa.si/view/{view_id}", headers=headers)
        
    except Exception:
        pass
    
    # try:
    #     resp = resp.text
    #     
    # except:
    #     resp = resp     
    
    return HTMLResponse(content=resp.text, status_code=200) #if page is None else Response(content=resp.text, media_type="application/xml")


@app.get("/download/{torrent}", response_class=Response)
async def getter(torrent: str | None = None) -> Response:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/download/{torrent}", headers=headers)

    except Exception:
        pass

    return Response(content=resp.text, media_type="application/x-bittorrent")


@app.get("/user/{username}", response_class=HTMLResponse)
async def getter(username: str | None = None) -> HTMLResponse:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/user/{username}", headers=headers)

    except Exception:
        pass

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/rules", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/rules", headers=headers)

    except Exception:
        pass

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/help", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    # resp = ""
    resp = await redis_cache.get(redis, "help")
    # print(resp)
    # resp = httpx.get(f"https://nyaa.si/help", headers=headers)
    if resp is None:
        try:
            resp = httpx.get(f"https://nyaa.si/help", headers=headers)
            await redis_cache.set(redis, "help", HTMLResponse(content=resp.text, status_code=200), ttl=86400, ignore_if_exists=False)

        except Exception as e:
            raise e

    else:
        return resp

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/login", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/login", headers=headers)

    except Exception:
        pass

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/register", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/register", headers=headers)

    except Exception:
        pass

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/upload", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/upload", headers=headers)

    except Exception:
        pass

    return HTMLResponse(content=resp.text, status_code=200)


if __name__ == '__main__':
   run("main:app", host="127.0.0.1", port=8000, reload=True)

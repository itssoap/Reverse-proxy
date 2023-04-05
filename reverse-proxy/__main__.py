from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
import httpx
import os
import aioredis
import datetime
import psutil
import sys

# logging
import logging
from loguru import logger

from utils import (
    StubbedGunicornLogger,
    InterceptHandler,
    StandaloneApplication,
    RedisCache,
)


headers = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://nyaa.si/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit\
        /537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Access-Control-Allow-Origin": "http://127.0.0.1:8000",
}


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

redis_cache = RedisCache()
redis = aioredis.Redis()

json_logs = False  # set it to True if you don't love yourselves
log_level = logging.getLevelName("INFO")


@app.on_event("startup")
def startup():
    load_dotenv()
    global redis_cache, redis
    redis_cache = RedisCache()
    redis = aioredis.from_url(os.getenv("REDIS_URL"), decode_responses=True)


@app.get("/", response_model=None, response_class=Response)
async def getter(request: Request) -> Response:  # type: ignore
    resp = httpx.Response(status_code=404, text="Default")
    params = request.query_params
    try:
        if params is not None:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"https://nyaa.si/?{params}", headers=headers)
            resp.raise_for_status()

        else:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://nyaa.si/", headers=headers)
            resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(
            f"[{log_time}] [/] HTTP Exception for {exc.request.url} - {exc}", flush=True
        )

    flag = 0

    try:
        _ = params["page"]
    except KeyError:
        flag = 1

    # returning a Respone class with media_type HTML
    # to avoid using Union of HTMLResponse and Response

    # The Union breaks the endpoint /docs, as it tries to look up
    # media_type json for openapi.json

    return (
        Response(content=resp.text, status_code=200, media_type="text/html")
        if flag == 1
        else Response(content=resp.text, media_type="application/xml")
    )


@app.get("/view/{view_id}", response_class=HTMLResponse)
async def getter(view_id: int | None = None) -> HTMLResponse:  # type: ignore
    resp = httpx.Response(status_code=404, text="Default")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://nyaa.si/view/{view_id}", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(
            f"[{log_time}] [/view/] HTTP Exception for {exc.request.url} - {exc}",
            flush=True,
        )

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/download/{torrent}", response_class=Response)
async def getter(torrent: str | None = None) -> Response:  # type: ignore
    resp = httpx.Response(status_code=404, text="Default")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://nyaa.si/download/{torrent}", headers=headers
            )
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(
            f"[{log_time}] [/download/] HTTP Exception for {exc.request.url} - {exc}",
            flush=True,
        )

    return Response(content=resp.text, media_type="application/x-bittorrent")


@app.get("/user/{username}", response_class=HTMLResponse)
async def getter(username: str | None = None) -> HTMLResponse:  # type: ignore
    resp = httpx.Response(status_code=404, text="Default")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://nyaa.si/user/{username}", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(
            f"[{log_time}] [/user/] HTTP Exception for {exc.request.url} - {exc}",
            flush=True,
        )

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/rules", response_class=HTMLResponse)
async def getter() -> HTMLResponse:  # type: ignore
    resp = httpx.Response(status_code=404, text="Default")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://nyaa.si/rules", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(
            f"[{log_time}] [/rules/] HTTP Exception for {exc.request.url} - {exc}",
            flush=True,
        )

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/help", response_class=HTMLResponse)
async def getter() -> HTMLResponse:  # type: ignore
    resp = await redis_cache.get(redis, "help")

    if resp is None:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://nyaa.si/help", headers=headers)
            resp.raise_for_status()
            await redis_cache.set(
                redis,
                "help",
                HTMLResponse(content=resp.text, status_code=200),
                ttl=86400,
                ignore_if_exists=False,
            )

        except httpx.HTTPError as exc:
            log_time = datetime.datetime.now()
            print(
                f"[{log_time}] [/help/] HTTP Exception for {exc.request.url} - {exc}",
                flush=True,
            )

        except (aioredis.ConnectionError, aioredis.TimeoutError) as redexc:
            log_time = datetime.datetime.now()
            print(
                f"[{log_time}] [/help/] Redis Exception occurred - {redexc}", flush=True
            )

    else:
        return resp

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/login", response_class=HTMLResponse)
async def getter() -> HTMLResponse:  # type: ignore
    resp = httpx.Response(status_code=404, text="Default")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://nyaa.si/login", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(
            f"[{log_time}] [/login/] HTTP Exception for {exc.request.url} - {exc}",
            flush=True,
        )

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/register", response_class=HTMLResponse)
async def getter() -> HTMLResponse:  # type: ignore
    resp = httpx.Response(status_code=404, text="Default")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://nyaa.si/register", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(
            f"[{log_time}] [/register/] HTTP Exception for {exc.request.url} - {exc}",
            flush=True,
        )

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/upload", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    resp = httpx.Response(status_code=404, text="Default")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://nyaa.si/upload", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(
            f"[{log_time}] [/upload/] HTTP Exception for {exc.request.url} - {exc}",
            flush=True,
        )

    return HTMLResponse(content=resp.text, status_code=200)


if __name__ == "__main__":
    intercept_handler = InterceptHandler()
    logging.root.setLevel(log_level)
    seen = set()
    for name in [
        *logging.root.manager.loggerDict.keys(),
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            logging.getLogger(name).handlers = [intercept_handler]

    logger.configure(handlers=[{"sink": sys.stdout, "serialize": json_logs}])

    options = {
        "bind": "127.0.0.1:8000",
        "workers": len(psutil.Process().cpu_affinity()),  # type: ignore
        "accesslog": "-",
        "errorlog": "-",
        "worker_class": "uvicorn.workers.UvicornWorker",
        "logger_class": StubbedGunicornLogger,
        "reload": "True",
        "reload_engine": "inotify",  # requires inotify package
    }

    StandaloneApplication("__main__:app", options).run()

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
import httpx
import os
from aioredis import Redis, from_url, ConnectionError, TimeoutError
from redis_cache import RedisCache
import datetime
import psutil
from gunicorn.app.wsgiapp import WSGIApplication
import sys

# logging
import logging
from gunicorn.glogging import Logger
from loguru import logger

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

log_level = logging.getLevelName("INFO")
access_log_level = logging.getLevelName("INFO")
json_logs = False # set it to True if you don't love yourselves

@app.on_event("startup")
def startup():
    load_dotenv()
    global redis_cache, redis 
    redis_cache = RedisCache()
    redis = from_url(os.getenv("REDIS_URL"), decode_responses=True)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class StubbedGunicornLogger(Logger):
    def setup(self, cfg):
        handler = logging.NullHandler()
        self.error_logger = logging.getLogger("gunicorn.error")
        self.error_logger.addHandler(handler)
        self.access_logger = logging.getLogger("gunicorn.access")
        self.access_logger.addHandler(handler)
        self.error_logger.setLevel(log_level)
        self.access_logger.setLevel(access_log_level)


class StandaloneApplication(WSGIApplication):
    def __init__(self, app_uri, options=None):
        self.options = options or {}
        self.app_uri = app_uri
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)



@app.get("/", response_model=None, response_class=Response)
async def getter(request: Request) -> Response:
    resp = ""
    params = request.query_params
    try:
        if params is not None:
            resp = httpx.get(f"https://nyaa.si/?{params}", headers=headers)
            resp.raise_for_status()

        else:
            resp = httpx.get(f"https://nyaa.si/", headers=headers)
            resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(f"[{log_time}] [/] HTTP Exception for {exc.request.url} - {exc}", flush=True)

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
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/view/{view_id}", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(f"[{log_time}] [/view/] HTTP Exception for {exc.request.url} - {exc}", flush=True)

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/download/{torrent}", response_class=Response)
async def getter(torrent: str | None = None) -> Response:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/download/{torrent}", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(f"[{log_time}] [/download/] HTTP Exception for {exc.request.url} - {exc}", flush=True)

    return Response(content=resp.text, media_type="application/x-bittorrent")


@app.get("/user/{username}", response_class=HTMLResponse)
async def getter(username: str | None = None) -> HTMLResponse:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/user/{username}", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(f"[{log_time}] [/user/] HTTP Exception for {exc.request.url} - {exc}", flush=True)

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/rules", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/rules", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(f"[{log_time}] [/rules/] HTTP Exception for {exc.request.url} - {exc}", flush=True)

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/help", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    # resp = ""
    resp = await redis_cache.get(redis, "help")

    if resp is None:
        try:
            resp = httpx.get(f"https://nyaa.si/help", headers=headers)
            resp.raise_for_status()
            await redis_cache.set(redis, "help", HTMLResponse(content=resp.text, status_code=200), ttl=86400, ignore_if_exists=False)

        except httpx.HTTPError as exc:
            log_time = datetime.datetime.now()
            print(f"[{log_time}] [/help/] HTTP Exception for {exc.request.url} - {exc}", flush=True)

        except (ConnectionError, TimeoutError) as redexc:
            log_time = datetime.datetime.now()
            print(f"[{log_time}] [/help/] Redis Exception occurred - {redexc}", flush=True)

    else:
        return resp

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/login", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/login", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(f"[{log_time}] [/login/] HTTP Exception for {exc.request.url} - {exc}", flush=True)

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/register", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/register", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(f"[{log_time}] [/register/] HTTP Exception for {exc.request.url} - {exc}", flush=True)

    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/upload", response_class=HTMLResponse)
async def getter() -> HTMLResponse:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/upload", headers=headers)
        resp.raise_for_status()

    except httpx.HTTPError as exc:
        log_time = datetime.datetime.now()
        print(f"[{log_time}] [/upload/] HTTP Exception for {exc.request.url} - {exc}", flush=True)

    return HTMLResponse(content=resp.text, status_code=200)


if __name__ == '__main__':
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
        "workers": len(psutil.Process().cpu_affinity()),
        "accesslog": "-",
        "errorlog": "-",
        "worker_class": "uvicorn.workers.UvicornWorker",
        "logger_class": StubbedGunicornLogger,
        "reload": "True",
        "reload_engine": "inotify" # requires inotify package
    }

    StandaloneApplication("main:app", options).run()

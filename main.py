from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_redis_cache import FastApiRedisCache, cache
from fastapi.encoders import jsonable_encoder
import httpx
import os

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

LOCAL_REDIS_URL = "redis://default:ol7IhrdrAGZIqS3g8CDR@containers-us-west-97.railway.app:6054"

redis_cache = None

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup():
    global redis_cache 
    redis_cache = FastApiRedisCache()
    redis_cache.init(
        host_url=os.environ.get("REDIS_URL", LOCAL_REDIS_URL),
        ignore_arg_types=[Request, Response]
    )

@app.get("/", response_class=HTMLResponse)
async def getter(request: Request) -> str:
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
        
    return HTMLResponse(content=resp.text, status_code=200) if flag == 1 else Response(content=resp.text, media_type="application/xml")


@app.get("/view/{view_id}", response_class=HTMLResponse)
@cache()
async def getter(view_id:int | None = None):
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
    
    # except:
    #     resp = resp
        
    return HTMLResponse(content=resp.text, status_code=200) #if page is None else Response(content=resp.text, media_type="application/xml")
    
    
@app.get("/download/{torrent}", response_class=HTMLResponse)
async def getter(torrent:str | None = None) -> str:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/download/{torrent}", headers=headers)
        
    except Exception:
        pass
        
    return Response(content=resp.text, media_type="application/x-bittorrent")


@app.get("/user/{username}", response_class=HTMLResponse)
@cache()
async def getter(username:str | None = None) -> str:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/user/{username}", headers=headers)
        
    except Exception:
        pass
        
    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/rules", response_class=HTMLResponse)
@cache()
async def getter() -> str:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/rules", headers=headers)
        
    except Exception:
        pass
        
    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/help", response_class=HTMLResponse)
async def getter() -> str:
    resp = ""
    _, respo = redis_cache.check_cache("help")
    
    print(respo)
    if respo is None:
        try:
            resp = httpx.get(f"https://nyaa.si/help", headers=headers)
            
        except Exception:
            pass
    # res = HTMLResponse(content=resp.text, status_code=200)
    # res.body = jsonable_encoder({"status": "200"})
    # res.headers['content-type'] = 'application/json'
    
    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/login", response_class=HTMLResponse)
@cache()
async def getter() -> str:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/login", headers=headers)
        
    except Exception:
        pass
        
    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/register", response_class=HTMLResponse)
@cache()
async def getter() -> str:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/register", headers=headers)
        
    except Exception:
        pass
        
    return HTMLResponse(content=resp.text, status_code=200)


@app.get("/upload", response_class=HTMLResponse)
async def getter() -> str:
    resp = ""
    try:
        resp = httpx.get(f"https://nyaa.si/upload", headers=headers)

    except Exception:
        pass

    return HTMLResponse(content=resp.text, status_code=200)

```md
Disclaimer: This module has been made for educational purposes and serves as a Proof-of-concept of how a reverse proxy can be implemented and used. The author(s) do not condone or promote piracy in any form. Please use this repository judicially and under legal clauses of your host country.
```

# Reverse Proxy 🚀

![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

*An over-engineered Reverse-proxy implementation using `FastAPI` for the backend, `Redis` for the static-page caching, `gunicorn` and `uvicorn` to serve a uvloop-enabled multi-worker architecture, packaged using `Poetry`, written in Python with love.*

## Index

- [Requirements](#requirements)
- [Installation](#installation)
- [Run](#run)
- [Usage](#usage)
- [Advanced](#advanced)
- [Future plans](#future-plans)

## Requirements

- A server (UNIX support only due to `gunicorn`)
- Python 3.10+ (Usage of built-in unions instead from `typing` module)
- Poetry for Python (Handling dependencies and running the server)
- Redis Instance (**Optional**)

## Installation

The installation process is handled effortlessly with Poetry.

To install Poetry, follow https://python-poetry.org/docs/#installation

Once Poetry is installed:

- **Optional**: Initialize a virtual environment to install and run the dependencies
```properties
poetry shell
```

- Install all dependencies (`poetry.lock` is present in the repository to make sure the versions we install are the same)
```properties
poetry install
```

- That's it!

## Run
- First, edit the .env file properly and set the `REDIS_URL` variable. If you don't want to host your own Redis instance, you can create a free instance from [Railway](https://railway.app)

```properties
mv .env.sample .env
```

- Run the app using Poetry (python3 instead of python, depending on your system)
```properties
poetry run python reverse-proxy
```

- Or without it 
```properties
python reverse-proxy
```
## Usage
>By default, the proxy doesn't run as a daemon

- Using Screen
Run the proxy inside a UNIX Screen, so that you can let it run in the background.

- Using systemd service
Coming Soon!

- Inside a docker container
Coming Soon!

## Advanced
To run it as a daemon, add:
```json
"daemon": "True"
```
in `options` dict in `reverse-proxy/__main__.py:main`

> This repo might look like a reverse-proxy for a particular web address, but it is to show an example of how different end-points which may return different type of responses should be handled.

> To better understand how Redis caching can be enabled/used for certain end-points, please refer to the implementation of the `/help` end-point

## Future plans
- Dockerize for OS-agnostic run
- Improve how the number of workers is set
- Make a non-Redis version/Redis decorator with a bool switch
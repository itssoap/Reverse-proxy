FROM bitnami/python:3.10.10-debian-11-r16 as basepython

WORKDIR /app

RUN chmod 777 /app

COPY poetry.lock pyproject.toml ./

RUN apt-get update && apt-get install \
    --no-install-recommends \
    -y curl build-essential redis

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="$PATH:~/.local/bin"

RUN poetry config virtualenvs.create false \
    && poetry install --no-root

RUN redis-server --daemonize yes 

RUN redis-server --daemonize yes --port 6380


FROM basepython

WORKDIR /app

ADD .env.sample .env

COPY . .

ENV PYTHONPATH "${PYTHONPATH}:/app"

EXPOSE 8000

CMD ["bash", "start.sh"]
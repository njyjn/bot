FROM python:3.7-slim

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip pipenv
RUN pipenv install --system --deploy


ENTRYPOINT ["gunicorn", "-b", ":8080", "--worker-class", "aiohttp.GunicornWebWorker", "app:create_app"]

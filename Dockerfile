FROM python:3.7-slim

WORKDIR /app
COPY Pipfile Pipfile.lock /app/
RUN pip install pip pipenv==2018.11.26
RUN pipenv install --system --deploy --ignore-pipfile

COPY . /app/

ENTRYPOINT ["gunicorn", "-b", ":8080", "--worker-class", "aiohttp.GunicornWebWorker", "app:create_app"]

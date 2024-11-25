FROM python:3.11-slim

WORKDIR /starnavi

COPY requirements.txt ./requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

ENV DB_PATH=./db.sqlite
ENV SQL_INIT=./init.sql

RUN pytest

CMD ["fastapi", "run", "app/main.py"]

EXPOSE 8000
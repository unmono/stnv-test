FROM python:3.11-slim

WORKDIR /starnavi

COPY requirements.txt ./requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

ENV SECRET_KEY=SOME_SECRET_KEY
ENV DB_PATH=./db.sqlite
ENV SQL_INIT=./init.sql

CMD ["fastapi", "run", "app/main.py"]

EXPOSE 8000
FROM python:3.10.11-alpine3.18

WORKDIR /tagfs

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY ./server.py .
COPY ./client.py .
COPY ./app ./app

COPY ./test.py .

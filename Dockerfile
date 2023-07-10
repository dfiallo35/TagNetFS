FROM python:3.10.11-alpine3.18
WORKDIR /tagfs

# REQUIREMENTS
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

# FILES
COPY ./server.py .
COPY ./client.py .
COPY ./app ./app
COPY ./configs.json .
COPY ./configs.yml .

# TEST
COPY ./test ./test
COPY ./create_database.txt .
COPY ./test_commands.txt .
import os
from typing import List, Annotated
from fastapi import FastAPI, Form

from app.client.client import Client
from app.utils.constant import *


app = FastAPI()


@app.post('/add', summary='Copy the files to the system and assign them the tags')
def _add(
    file_list: Annotated[List[str], Form(...)],
    tag_list: Annotated[List[str], Form(...)],
):
    files = []
    for i in file_list:
        if not os.path.isfile(i):
            raise FileNotFoundError(i)
        with open(i, 'rb') as f:
            files.append((f.read(), os.path.basename(i)))
    
    Client.run((ADD, files, tag_list))

@app.delete('/delete', summary='Delete all the files that match the tag query')
def _delete(
    tag_query: Annotated[List[str], Form(...)],
):
    Client.run((DELETE, tag_query))

@app.get('/list/', summary='List the name and the tags of every file that match the tag query')
def _list(
    tag_query: Annotated[List[str], Form(...)],
):
    Client.run((LIST, tag_query))

@app.post('/add_tags', summary='Add the tags from the tag list to the files that match the tag query')
def _add_tags(
    tag_query: Annotated[List[str], Form(...)],
    tag_list: Annotated[List[str], Form(...)],
):
    Client.run((ADD_TAGS, tag_query, tag_list))

@app.delete('/delete_tags', summary='Delete the tags from the tag list to the files that match the tag query')
def _delete_tags(
    tag_query: Annotated[List[str], Form(...)],
    tag_list: Annotated[List[str], Form(...)],
):
    Client.run((DELETE_TAGS, tag_query, tag_list))

@app.get("/")
def main():
    return {'message': 'Hi'}

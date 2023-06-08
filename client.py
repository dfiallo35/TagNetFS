import typer
import socket
from typing import List
from fastapi import UploadFile

from app.utils.utils import *
from app.client.client import Client




app = typer.Typer()


@app.command()
def add(
    file_list: List[typer.FileBinaryRead] = typer.Option(..., '-fl', '--file-list'),
    tag_list: List[str] = typer.Option(..., '-tl', '--tag-list'),
):
    print()
    Client.run(('add', [UploadFile(file=i.read(), filename=i.name) for i in file_list], tag_list))


@app.command()
def delete(
    tag_query: List[str] = typer.Option(..., '-tq', '--tag-query'),
):
    Client.run(('delete', tag_query))


@app.command()
def list(
    tag_query: List[str] = typer.Option(..., '-tq', '--tag-query'),
):
    Client.run(('list', tag_query))


@app.command()
def add_tags(
    tag_query: List[str] = typer.Option(..., '-tq', '--tag-query'),
    tag_list: List[str] = typer.Option(..., '-tl', '--tag-list'),
):
    Client.run(('add-tags', tag_query, tag_list))


@app.command()
def delete_tags(
    tag_query: List[str] = typer.Option(..., '-tq', '--tag-query'),
    tag_list: List[str] = typer.Option(..., '-tl', '--tag-list'),
):
    Client.run(('delete-tags', tag_query, tag_list))




if __name__ == '__main__':
    app()
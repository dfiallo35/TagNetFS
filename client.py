import typer
import socket
from typing import List

from app.utils.utils import *
from app.client.client import Client




app = typer.Typer()


@app.command()
def add(
    file_list: List[str] = typer.Option(..., '-fl'),
    tag_list: List[str] = typer.Option(..., '-tl'),
):
    Client.run(('add', file_list, tag_list))


@app.command()
def delete(
    tag_query: List[str] = typer.Option(..., '-tq'),
):
    Client.run(('delete', tag_query))


@app.command()
def list(
    tag_query: List[str] = typer.Option(..., '-tq'),
):
    Client.run(('list', tag_query))


@app.command()
def add_tags(
    tag_query: List[str] = typer.Option(..., '-tq'),
    tag_list: List[str] = typer.Option(..., '-tl'),
):
    Client.run(('add-tags', tag_query, tag_list))


@app.command()
def delete_tags(
    tag_query: List[str] = typer.Option(..., '-tq'),
    tag_list: List[str] = typer.Option(..., '-tl'),
):
    Client.run(('delete-tags', tag_query, tag_list))




if __name__ == '__main__':
    app()
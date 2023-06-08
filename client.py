import os
import typer
from typing import List

from app.utils.utils import *
from app.client.client import Client




app = typer.Typer()


@app.command()
def add(
    file_list: List[str] = typer.Option(..., '-f', '--file-list'),
    tag_list: List[str] = typer.Option(..., '-t', '--tag-list'),
):
    files = []
    for i in file_list:
        if not os.path.isfile(i):
            raise FileNotFoundError(i)
        with open(i, 'r') as f:
            files.append((f.read(), os.path.basename(i)))
    
    Client.run(('add', files, tag_list))


@app.command()
def delete(
    tag_query: List[str] = typer.Option(..., '-q', '--tag-query'),
):
    Client.run(('delete', tag_query))


@app.command('list')
def qist(
    tag_query: List[str] = typer.Option(..., '-q', '--tag-query'),
):
    Client.run(('list', tag_query))


@app.command()
def add_tags(
    tag_query: List[str] = typer.Option(..., '-q', '--tag-query'),
    tag_list: List[str] = typer.Option(..., '-t', '--tag-list'),
):
    Client.run(('add-tags', tag_query, tag_list))


@app.command()
def delete_tags(
    tag_query: List[str] = typer.Option(..., '-q', '--tag-query'),
    tag_list: List[str] = typer.Option(..., '-t', '--tag-list'),
):
    Client.run(('delete-tags', tag_query, tag_list))




if __name__ == '__main__':
    app()
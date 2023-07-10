import os
import typer
from typing import List

from app.utils.utils import *
from app.client.client import Client
from app.utils.constant import *
import api




app = typer.Typer()


@app.command()
def add(
    file_list: List[str] = typer.Option(..., '-f', '--file-list'),
    tag_list: List[str] = typer.Option(..., '-t', '--tag-list'),
):
    api._add(file_list, tag_list)


@app.command()
def delete(
    tag_query: List[str] = typer.Option(..., '-q', '--tag-query'),
):
    api._delete(tag_query)


@app.command('list')
def qlist(
    tag_query: List[str] = typer.Option(..., '-q', '--tag-query'),
):
    api._list(tag_query)


@app.command()
def add_tags(
    tag_query: List[str] = typer.Option(..., '-q', '--tag-query'),
    tag_list: List[str] = typer.Option(..., '-t', '--tag-list'),
):
    api._add_tags(tag_query, tag_list)

@app.command()
def delete_tags(
    tag_query: List[str] = typer.Option(..., '-q', '--tag-query'),
    tag_list: List[str] = typer.Option(..., '-t', '--tag-list'),
):
    api._delete_tags(tag_query, tag_list)




if __name__ == '__main__':
    app()  
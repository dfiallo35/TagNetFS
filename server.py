import typer
import socket
from typing import List

from app.utils.utils import *
from app.server.server import Server
from app.client.client import Client


app = typer.Typer()



@app.command()
def server(
    nbits: int = typer.Option(8, '-b', '--n-bits', help='')
):
    server = Server(nbits)
    server.run()


if __name__ == '__main__':
    app()

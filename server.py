import typer
import socket
from typing import List

from app.utils.utils import *
from app.server.server import Server
from app.client.client import Client

# TODO: partitionate the network

app = typer.Typer()



@app.command()
def server(
    succ: str = typer.Option(socket.gethostbyname(socket.gethostname()), '-s', '--server', help=''),
    nbits: int = typer.Option(8, '-b', '--n-bits', help='')
):
    server = Server(succ, nbits)
    server.run()


if __name__ == '__main__':
    app()

import typer
import socket
from typing import List

from app.utils.utils import *
from app.chord.chord import ChordNode
from app.client.client import Client


app = typer.Typer()



@app.command()
def server(
    address: List[str] = typer.Option([], '-a', '--addr', help='IP:PORT of servers to connect.'),
    nbits: int = typer.Option(8, '-b', '--n-bits', help='')
):
    
    print('Chord node started.')
    print('hosts', address)

    HOST = socket.gethostbyname(socket.gethostname())
    PORT = 9090
    id = hashing(nbits, '{}:{}'.format(HOST, PORT))

    node = ChordNode(id, nbits)
    node.run(hashing_address(nbits, address))


@app.command()
def client(
    address: str = typer.Option(..., '-a', '--addr', help='IP:PORT of server to connect.'),
):
    client = Client(*address.split(':'))
    client.run()



if __name__ == '__main__':
    # server(['10.0.0.2:9090', '10.0.0.3:9090'], 8)
    app()

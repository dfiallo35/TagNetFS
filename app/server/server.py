import rpyc
import socket
import asyncio


@rpyc.service
class Server(rpyc.Service):
    def __init__(self):
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.PORT = 9090



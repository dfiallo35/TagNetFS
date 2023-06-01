import rpyc
from rpyc import Connection
import socket
from app.utils.utils import *

class Client:
    def __init__(self, host: str, port: int) -> None:
        self.SERVER_HOST = host
        self.SERVER_PORT = port
        self.SERVER_ADDR = (self.SERVER_HOST, self.SERVER_PORT)
    

    def run(self):
        while True:
            conn: Connection = rpyc.connect(*self.SERVER_ADDR)
            
            data = input('>>>')
            conn.root.add(data)
            print(conn.root.get())
            conn.close()

    
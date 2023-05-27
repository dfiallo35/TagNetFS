import Pyro4
import socket
from app.utils.utils import *

class Client:
    def __init__(self, host: str, port: int) -> None:
        self.HOST = host
        self.PORT = port
        self.ADDR = (self.HOST, self.PORT)
    
    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.ADDR)
        for i in range(20):
            s.sendto(encode_message(Message.message), self.ADDR)



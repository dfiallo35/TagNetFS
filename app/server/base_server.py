import socket
from app.utils.utils import *



# TODO: Should receive request from clients and send it to servers
# TODO: Base server
# TODO: Dispatcher
# TODO: Worker servers
# TODO: Storage servers

# TODO: Stalker: structure to check live IP and ports
# TODO: Connect server Worker with client through Dispatcher

class BaseServer:
    def __init__(self) -> None:
        # Address
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.PORT = 9090
        self.ADDR = (self.HOST, self.PORT)
        # Socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Address: -host {} -port {}'.format(*self.ADDR))

    
    def run(self):
        '''Run server.'''
        ...
            
    
    def receive(self, _socket: socket, size:int):
        '''Receive data.'''
        data = _socket.recv(size)
        return data
    
    def send(self):
        ...

    def accept(self):
        '''Accept connection with server.'''
        print('waiting...')
        c, c_addr = self.socket.accept()
        print('Server {} connected to {}'.format(self.ADDR, c_addr))
        return c, c_addr

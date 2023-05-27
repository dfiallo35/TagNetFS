import time
import socket

from app.server.base_server import BaseServer
from app.utils.utils import *


class Server(BaseServer):
    def run(self):
        '''
        Run server.
        '''
        self.socket.bind(self.ADDR)
        
        
        while True:
            time.sleep(0.01)
            self.socket.listen(10)
            c, c_addr = self.accept()
            for i in range(10):
                message = self.receive(c, 1024)
                match decode_message(message):
                    case Message.message:
                        print(Message.message)
                    case Message.uri:
                        print(Message.uri)
                    case _:
                        print(None)
        




if __name__ == '__main__':
    # import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--host', type=str, required=True)
    # parser.add_argument('--port', type=int, required=True)
    # args = parser.parse_args()
    
    # #TODO: Should be de host and port to connect
    # #TODO: Shlould be de main server
    # HOST = args.host
    # PORT = args.port

    server = Server()
    server.run()
        


    

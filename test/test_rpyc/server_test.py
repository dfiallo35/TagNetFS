import rpyc
from rpyc.utils.server import ThreadedServer
# page 204
import socket

SERVER = '10.0.0.2'
PORT = 9090



@rpyc.service
class DBList(rpyc.Service):
    def __init__(self) -> None:
        self._value = []

    @rpyc.exposed
    def value(self):
        return self._value

    @rpyc.exposed
    def append(self, data):
        self._value.extend(str(data))
        return self._value


class Server:
    def __init__(self):
        self.server = ThreadedServer(DBList, hostname=SERVER, port=PORT)

    def start(self):
        self.server.start()


s = Server()
s.start()

import Pyro5.api
import Pyro5.core
import Pyro5.server
import Pyro5.client
import Pyro5.nameserver
from threading import Thread
import socket
from app.utils.thread import Kthread


import Pyro5.api
from Pyro5.api import Proxy
from Pyro5.nameserver import NameServer


@Pyro5.api.expose
class GreetingMaker:
    def get_fortune(self, name):
        return "Hello, {0}. Here is your fortune message:\n" \
               "Tomorrow's lucky number is 12345678.".format(name)



class A:
    def __init__(self, ip: str, port: int):
        self.id = ...
        self.IP = ip
        self.PORT = port

        self.daemon = Pyro5.api.Daemon(self.IP, self.PORT)
        self.daemon_thread = Kthread(
                    target=self.daemon.requestLoop,
                    daemon=True
                )
        self.daemon_thread.start()

        # TODO: what to do with ns
        self.ns: NameServer|Proxy = Pyro5.api.locate_ns()
    
    def run_daemon(self):
        self.daemon_thread.start()

    def register(self, name: str, f):
        uri = self.daemon.register(f)
        self.ns.register(name, uri)

a = A(socket.gethostbyname(socket.gethostname()), 8876)
a.register('a', GreetingMaker)


while True: ...
import sys
import socket
from Pyro5.nameserver import NameServerDaemon
from Pyro5.nameserver import BroadcastServer
from app.utils.thread import Kthread

class Leader:
    def __init__(self, ip: str, port: str):
        self.id = ...
        self.IP = ip
        self.PORT = port

        self.daemon = NameServerDaemon(self.IP, self.PORT)
        self.ns = Kthread(
            target=self.daemon.requestLoop,
            daemon=True
        )
        self.ns.start()

        self.nsUri = self.daemon.uriFor(self.daemon.nameserver)
        self.internalUri = self.daemon.uriFor(self.daemon.nameserver, nat=False)

        self.bcserver = BroadcastServer(self.nsUri)
        print("Broadcast server running on {}".format(self.bcserver.locationStr))
        self.bcserver.runInThread()
        
        print("NS running on {}".format(str(self.daemon.locationStr)))
        print('URI = {}'.format(self.nsUri))
        sys.stdout.flush()
    
    def run_ns(self):
        self.ns = Kthread(
            target=self.daemon.requestLoop,
            daemon=True
        )
        self.ns.start()
    
    def kill_ns(self):
        self.ns.kill()
        self.ns.join()
    
    def register(self, name: str, f):
        uri = self.daemon.register(f)
        self.daemon.nameserver.register(name, uri)


a = Leader(socket.gethostbyname(socket.gethostname()), 8979)
# a.register('a', GreetingMaker)


# ns = Pyro5.api.locate_ns()

# daemon = Pyro5.api.Daemon(socket.gethostbyname(socket.gethostname()), 8979)
# uri = daemon.register(GreetingMaker)
# ns.register(uri)

while True: ...

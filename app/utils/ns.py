import sys
import Pyro5.api
from Pyro5.api import Daemon, Proxy
from Pyro5.nameserver import NameServer, NameServerDaemon, BroadcastServer
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
        print('URI = {}\n'.format(self.nsUri))
        sys.stdout.flush()
    
    def run_ns(self):
        self.ns.start()
    
    def kill_ns(self):
        self.ns.kill()
        self.ns.join()
    
    def register(self, name: str, f):
        uri = self.daemon.register(f)
        self.daemon.nameserver.register(name, uri)



class Node:
    def __init__(self, ip: str, port: int):
        self.id = ...
        self.IP = ip
        self.PORT = port

        self.daemon = Daemon(self.IP, self.PORT)
        self.daemon_thread = Kthread(
                    target=self.daemon.requestLoop,
                    daemon=True
                )
        self.daemon_thread.start()
        print("Node running on {}".format(str(self.daemon.locationStr)))

        # TODO: what to do with ns
        self.ns: NameServer|Proxy = Pyro5.api.locate_ns()
        print('Node connected to {}\n'.format(self.ns._pyroUri.host))
    
    def run_daemon(self):
        self.daemon_thread.start()

    def register(self, name: str, f):
        uri = self.daemon.register(f)
        self.ns.register(name, uri)
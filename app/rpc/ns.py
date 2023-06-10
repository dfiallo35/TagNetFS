import sys
import socket
import logging
import contextlib
from Pyro5 import config
from Pyro5 import socketutil
from Pyro5.api import Daemon
from Pyro5.client import Proxy
from Pyro5.nameserver import NameServerDaemon, BroadcastServer

from app.utils.thread import Kthread



class Leader:
    def __init__(self, ip: str, port: str):
        self.id = ...
        self.IP = ip
        self.PORT = port

        self.daemon = NameServerDaemon(self.IP, self.PORT)
        self.daemon_thread = Kthread(
            target=self.request,
            daemon=True
        )
        self.daemon_thread.start()

        self.nsUri = self.daemon.uriFor(self.daemon.nameserver)
        self.internalUri = self.daemon.uriFor(self.daemon.nameserver, nat=False)

        self.bcserver = BroadcastServer(self.nsUri)
        print("Broadcast server running on {}".format(self.bcserver.locationStr))
        self.bcserver.runInThread()
        
        print("NS running on {}".format(str(self.daemon.locationStr)))
        print('URI = {}\n'.format(self.nsUri))
        sys.stdout.flush()
    
    def request(self):
        try:
            self.daemon.requestLoop()
        finally:
            self.daemon.close()
            if self.bcserver is not None:
                self.bcserver.close()
        print("NS shut down.")
    
    def run_daemon(self):
        self.daemon_thread.start()
    
    def kill_daemon(self):
        # self.daemon.shutdown()
        self.daemon.close()
        if self.bcserver is not None:
            self.bcserver.close()
        self.daemon_thread.join()
    
    def register(self, name: str, f):
        uri = self.daemon.register(f, force=True)
        self.daemon.nameserver.register(name, uri)



class Node:
    def __init__(self, ip: str, port: int):
        self.id = ...
        self.IP = ip
        self.PORT = port

        self.daemon = Daemon(self.IP, self.PORT)
        self.daemon_thread = Kthread(
            target=self.request,
            daemon=True
        )
        self.daemon_thread.start()
        print("Node running on {}".format(str(self.daemon.locationStr)))

        # TODO: what to do with ns
        self.ns: Proxy = locate_ns()
        print('Node connected to {}\n'.format(self.ns._pyroUri.host))
    
    def request(self):
        try:
            self.daemon.requestLoop()
        finally:
            self.daemon.close()
        print("NS shut down.")

    def run_daemon(self):
        self.daemon_thread.start()
    
    def kill_daemon(self):
        # self.daemon.shutdown()
        self.daemon.close()
        self.daemon_thread.join()

    def register(self, name: str, f):
        uri = self.daemon.register(f, force=True)
        self.ns.register(name, uri)



def locate_ns() -> Proxy:
    port = config.NS_BCPORT
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    with contextlib.suppress(Exception):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    sock.settimeout(0.7)
    
    ns = []
    for _ in range(3):
        try:
            for bcaddr in config.BROADCAST_ADDRS:
                try:
                    sock.sendto(b"GET_NSURI", 0, (bcaddr, port))
                except socket.error as x:
                    err = getattr(x, "errno", x.args[0])
                    if err not in socketutil.ERRNO_EADDRNOTAVAIL and err not in socketutil.ERRNO_EADDRINUSE:
                        raise
            while True:
                try:
                    data, _ = sock.recvfrom(100)
                    text = data.decode("iso-8859-1")
                    ns.append(text)
                except socket.timeout:
                    if ns:
                        sock.close()
                        ns = list(set(ns))
                        ns.sort()
                        proxy = Proxy(ns[0])
                        return proxy
                    else:
                        break
        except socket.timeout:
            continue
    with contextlib.suppress(OSError, socket.error):
        sock.shutdown(socket.SHUT_RDWR)
    sock.close()
    return None


def connect(ns: Proxy, name: str) -> Proxy:
    '''
    Get the element registered in the ns with the given name.
    '''
    uri = ns.lookup(name)
    f = Proxy(uri)
    return f
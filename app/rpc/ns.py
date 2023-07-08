import sys
import socket
import logging
import contextlib
from time import sleep

import Pyro5.errors
from Pyro5 import config
from Pyro5 import socketutil
from Pyro5.api import Daemon
from Pyro5.client import Proxy
from Pyro5.nameserver import NameServerDaemon, BroadcastServer

from app.utils.thread import Kthread
from app.utils.constant import *
from app.server.base_server import BaseServer
from app.utils.utils import read_config


class Leader(BaseServer):
    def __init__(self, ip: str, port: str):
        self.id = ...
        self.IP = ip
        self.PORT = port

        # self._timeout = 1
        self._timeout = read_config()["global_timeout"]

        self.daemon = NameServerDaemon(self.IP, self.PORT)
        self.daemon_thread = Kthread(
            target=self.request,
            daemon=True
        )
        self.daemon_thread.start()

        self.nsUri = self.daemon.uriFor(self.daemon.nameserver)
        self.internalUri = self.daemon.uriFor(
            self.daemon.nameserver, nat=False)

        self.bcserver = BroadcastServer(self.nsUri, '10.0.255.255')
        # print("Broadcast server running on {}".format(self.bcserver.locationStr))
        self.bcserver.runInThread()

        # print("NS running on {}".format(str(self.daemon.locationStr)))
        # print('URI = {}\n'.format(self.nsUri))
        sys.stdout.flush()

        # PING
        self._ping_thread = Kthread(
            target=self.ping_alive,
            daemon=True
        )
        self._ping_thread.start()
    
    def ping(self):
        return PING

    def request(self):
        try:
            self.daemon.requestLoop()
        finally:
            self.daemon.shutdown()
            self.daemon.close()
            if self.bcserver is not None:
                self.bcserver.close()
        print("NS shut down.")

    def run_daemon(self):
        self.daemon_thread.start()

    def kill_daemon(self):
        try:
            self.daemon.shutdown()
            self.daemon.close()
            if self.bcserver is not None:
                self.bcserver.close()
        except:
            pass
        
    
    def kill_threads(self):
        try:
            self.daemon_thread.kill()
            if self.daemon_thread.is_alive():
                self.daemon_thread.join()
            self._ping_thread.kill()
            if self._ping_thread.is_alive():
                self._ping_thread.join()
        except:
            pass
    
    def register(self, name: str, f, id: str=None):
        uri = self.daemon.register(f, force=True)
        self.daemon.nameserver.register(name, uri)

    def ping_alive(self):
        '''
        Ping all the workers and unregister the dead ones.
        '''
        while True:
            try:
                ns = locate_ns()
                objects = list(ns.list().items())
                for name, uri in objects:
                    try:
                        p = direct_connect(uri)
                        p.ping()
                    except Pyro5.errors.PyroError:
                        print(f"Object {name} is not alive, unregistering...")
                        ns.remove(name)
                sleep(self._timeout)
            except Pyro5.errors.NamingError:
                sleep(self._timeout)



class Node(BaseServer):
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

    def ping(self):
        return PING

    def request(self):
        try:
            self.daemon.requestLoop()
        finally:
            self.daemon.close()
        print("NS shut down.")

    def run_daemon(self):
        self.daemon_thread.start()

    def kill_daemon(self):
        try:
            self.daemon.close()
        except:
            pass
    
    def kill_threads(self):
        try:
            self.daemon_thread.kill()
            if self.daemon_thread.is_alive():
                self.daemon_thread.join()
        except:
            pass
    
    # FIX: update ns?
    def register(self, name: str, f, id: str=None):
        uri = self.daemon.register(f, force=True, objectId=id)
        self.ns.register(name, uri)
        return uri


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
            for bcaddr in ['10.0.255.255']:
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
    raise Pyro5.errors.NamingError


def connect(ns: Proxy, name: str) -> Proxy:
    '''
    Get the element registered in the ns with the given name.
    '''
    uri = ns.lookup(name)
    f = Proxy(uri)
    return f


def direct_connect(uri: str):
    '''
    Get the element registered in the ns with the given uri.
    '''
    f = Proxy(uri)
    return f

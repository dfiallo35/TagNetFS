import rpyc

import socket
from time import sleep

import Pyro5.api
import Pyro5.server
import Pyro5.errors
import Pyro5.nameserver
from Pyro5.nameserver import NameServer
from Pyro5.api import URI, Proxy

from app.utils.utils import hash
from app.utils.thread import Kthread
from app.server.worker import Worker
from app.server.dispatcher import Dispatcher


from app.utils.ns import Leader, Node



# NOTE: New idea with Pyro5
# TODO: create a var for election
# TODO: duning election cant change the functionality of server



class Server():
    def __init__(self, nbits: int = 8):
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.PORT = 9090
        self.id = hash(nbits, self.HOST)
        self.nbits = nbits

        self.coordinator: Server = None
        self.timeout: int = 10
        self.ns = None
        self.elections: Kthread = None

        self.server = None

    
    def run(self):
        '''
        Run the node.
        '''
        # self.elections = Kthread(
        #     target=self.run_elections,
        #     daemon=True
        # )
        # self.elections.start()


        try:
            ns = Pyro5.api.locate_ns()
            self.ns = Node(self.HOST, self.PORT)
            self.server = Worker()
            self.ns.register(str(self.id), self.server)
        except Pyro5.errors.NamingError:
            self.ns = Leader(self.HOST, self.PORT)
            self.server = Dispatcher()
            self.ns.register('request', self.server)


        while True:
            # TODO: If leader get Dispatcher, else others functionalities
            ...


    ########### ELECTIONS ###########

    def run_elections(self):
        '''
        Run the elections in bg.
        '''
        while True:
            sleep(self.timeout)
            print('Running election...\n')
            self.election()
            
            try:
                ns: NameServer|Proxy = Pyro5.api.locate_ns()
                ns_host = ns._pyroUri.host
                if ns_host != self.HOST:
                    if ns.list().get(str(self.id)) is None:
                        ns.register(str(self.id), self.create_ns())
            except OSError:
                self.create_ns()


    def find_coordinator(self):
        '''
        Find the coordinator.
        '''
        if self.coordinator:
            try:
                ns: NameServer|Proxy = Pyro5.api.locate_ns()
                ns_host = ns._pyroUri.host
                if self.coordinator.HOST != ns_host:
                    coordinator: rpyc.Connection = rpyc.connect(ns._pyroUri.host, ns._pyroUri.port)
                    return coordinator.root
                return self.coordinator
            except OSError:
                print(f"Node {self.id}: Coordinator {self.coordinator.id} is down")
        return self


    def election(self):
        '''
        Go elections.
        '''
        coordinator = self.find_coordinator()

        if coordinator.id == self.id:
            if not self.is_alive():
                self.coordinator = self
                self.create_ns()
                
                print(f"Node {self.id} is the new coordinator")

        else:
            self.set_coordinator(coordinator)

    
    def set_coordinator(self, coordinator):
        '''
        If self Kthread with the self ns is alive then kill it, and then set the coordinator.
        '''
        if self.is_alive():
            self.kill
        self.coordinator = coordinator

    
    def generate_uri(self):
        '''
        Generate self URI.
        '''
        return 'PYRONAME:{}@{}:{}'.format(str(self.id), str(self.HOST), str(self.PORT))

    
    def create_ns(self):
        '''
        Create self ns.
        '''
        self.ns = Kthread(
            target=lambda h, p: Pyro5.nameserver.start_ns_loop(h, p),
            args=(self.HOST, self.PORT),
            daemon=True
        )
        self.ns.start()
    
    
    def is_alive(self):
        '''
        Return if Kthread with the self ns is alive or not.
        '''
        try:
            return self.ns.is_alive()
        except AttributeError:
            return False

    
    def kill(self):
        '''
        Kill the Kthread with self ns.
        '''
        self.ns.kill()
        self.ns.join()



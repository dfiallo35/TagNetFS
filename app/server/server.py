import socket
import logging
from time import sleep

import Pyro5.api
import Pyro5.server
import Pyro5.errors
import Pyro5.nameserver

from app.rpc.ns import *
from app.utils.utils import hash
from app.utils.thread import Kthread
from app.server.worker import Worker
from app.server.dispatcher import Dispatcher




# Create and configure logger
logging.basicConfig(
    # filename="server.log",
    # encoding='utf-8',
    # filemode='w',
    format='%(asctime)s %(message)s',
    level=logging.DEBUG
)



# NOTE: New idea with Pyro5
# TODO: create a var for election
# TODO: duning election cant change the functionality of server

# TODO: Delete dead nodes. Unregister
# TODO: Save in db all the directions of the files. New table


# NOTE: Seems to be solved
# BUG: When you close the coordinator server dunning the election of other node, that node crash


@Pyro5.api.expose
class Server():
    def __init__(self, nbits: int = 8):
        self._host = socket.gethostbyname(socket.gethostname())
        self._port = 9090
        self._id = hash(nbits, self._host)
        self._nbits = nbits
        logging.info('Node name: {}'.format(self.node_name))

        self._alive = True
        self._timeout: int = 10
        self._in_elections = False
        self._elections: Kthread = None
        self._coordinator: Server = None
        
        self._server = None
        self._root = None

    
    def a(self):
        return 1
    
    @property
    def id(self):
        return self._id
    
    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def node_name(self):
        return 'node-{}'.format(str(self.id))
    
    @property
    def worker_name(self):
        return 'worker-{}'.format(str(self.id))
    
    @property
    def is_alive(self):
        return self._alive

    @property
    def in_elections(self):
        return self._in_elections
    

    def run(self):
        '''
        Run the node.
        '''
        self._elections = Kthread(
            target=self.run_elections,
            daemon=True
        )
        self._elections.start()

        while True:
            sleep(1)


    def become_leader(self):
        self.kill()
        self._server = Leader(self._host, self._port)
        self._root = Dispatcher()
        self._server.register('leader', self)
        self._server.register('request', self._root)
        logging.info('Node: {} become leader\n'.format(self.node_name))

    def become_node(self):
        self.kill()
        self._server = Node(self._host, self._port)
        self._root = Worker()
        self._server.register(self.node_name, self)
        self._server.register(self.worker_name, self._root)
        logging.info('Node: {} become worker\n'.format(self.node_name))
    
    def locate_ns(self):
        try:
            ns = locate_ns()
        except Pyro5.errors.NamingError:
            ns = None
        return ns


    ########### ELECTIONS ###########

    def run_elections(self):
        '''
        Run the elections loop.
        '''
        while True:
            logging.info('Running election...\n')
            ns = locate_ns()
            try:
                if not self._coordinator or not self._coordinator.is_alive:
                    self.election()
                else:
                    if ns and ns._pyroUri.host != self._coordinator.host:
                        self.election()
            except Pyro5.errors.PyroError:
                self.election()
            
            logging.info('Election end\n')
            sleep(self._timeout)
    

    def find_coordinator(self):
        '''
        Find the coordinator.
        '''
        try:
            if not self._coordinator or not self._coordinator.is_alive:
                ns = locate_ns()
                if ns:
                    coordinator = connect(ns, 'leader')
                    return coordinator
                else:
                    return self
            else:
                ns = locate_ns()
                if ns and ns._pyroUri.host != self._coordinator.host:
                    coordinator = connect(ns, 'leader')
                    return coordinator
                else:
                    return self._coordinator
                    
        except Pyro5.errors.PyroError:
            ns = locate_ns()
            if ns:
                coordinator = connect(ns, 'leader')
                return coordinator
            else:
                return self


    def election(self):
        '''
        Go elections.
        '''
        self._in_elections = True
        coordinator = self.find_coordinator()
        self._coordinator = coordinator
        
        try:
            if self._coordinator.id == self.id:
                self.become_leader()
                logging.info("Node {} is the new coordinator".format(self.node_name))
            else:
                self.become_node()
        except Pyro5.errors.PyroError:
            self.election()
        self._in_elections = False

    
    def kill(self):
        '''
        kill server.
        '''
        try:
            self._server.kill_daemon()
            self._server = None
        except:
            self._server = None
    



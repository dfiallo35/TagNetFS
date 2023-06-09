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

# BUG: When you close the coordinator server dunning the election of other node, that node crash


@Pyro5.api.expose
class Server():
    def __init__(self, nbits: int = 8):
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.PORT = 9090
        self._id = hash(nbits, self.HOST)
        self.nbits = nbits
        logging.info('Node name: {}'.format(self.node_name))

        self.alive = True
        self.timeout: int = 10
        self._in_elections = False
        self.elections: Kthread = None
        self.coordinator: Server = None
        
        self.server = None
        self.function = None

    
    @property
    def id(self):
        return self._id
    
    @property
    def host(self):
        return self.HOST

    @property
    def port(self):
        return self.PORT

    @property
    def node_name(self):
        return 'node-{}'.format(str(self.id))
    
    @property
    def is_alive(self):
        return self.alive

    @property
    def in_elections(self):
        return self._in_elections
    

    def run(self):
        '''
        Run the node.
        '''
        self.elections = Kthread(
            target=self.run_elections,
            daemon=True
        )
        self.elections.start()

        while True:
            sleep(1)


    def become_leader(self):
        self.kill()
        self.server = Leader(self.HOST, self.PORT)
        self.function = Dispatcher()
        self.server.register('leader', self)
        logging.info('Node: {} become leader\n'.format(self.node_name))

    def become_node(self):
        self.kill()
        self.server = Node(self.HOST, self.PORT)
        self.function = Worker()
        self.server.register(self.node_name, self)
        logging.info('Node: {} become worker\n'.format(self.node_name))


    ########### ELECTIONS ###########

    def run_elections(self):
        '''
        Run the elections in bg.
        '''
        while True:
            logging.info('Running election...\n')
            
            try:
                ns = locate_ns()
            except Pyro5.errors.NamingError:
                ns = None
            
            try:
                if not self.coordinator or not self.coordinator.is_alive:
                    self.election(ns)
                else:
                    if ns and ns._pyroUri.host != self.coordinator.host:
                        self.election(ns)

            except Pyro5.errors.PyroError:
                self.election(ns)
            
            logging.info('Election end\n')
            sleep(self.timeout)
    

    def find_coordinator(self, ns: Proxy):
        '''
        Find the coordinator.
        '''
        try:
            if not self.coordinator or not self.coordinator.is_alive:
                if ns:
                    coordinator = connect(ns, 'leader')
                    return coordinator
                else:
                    return self
            else:
                if ns and ns._pyroUri.host != self.coordinator.host:
                    coordinator = connect(ns, 'leader')
                    return coordinator
                else:
                    return self.coordinator
                    
        except Pyro5.errors.PyroError:
            if ns:
                coordinator = connect(ns, 'leader')
                return coordinator
            else:
                return self


    def election(self, ns: Proxy):
        '''
        Go elections.
        '''
        self._in_elections = True
        coordinator = self.find_coordinator(ns)
        self.coordinator = coordinator
        
        if self.coordinator.id == self.id:
            self.become_leader()
            logging.info("Node {} is the new coordinator".format(self.node_name))
        else:
            self.become_node()
        self._in_elections = False

    
    def kill(self):
        '''
        kill server.
        '''
        try:
            self.server.kill_daemon()
            self.server = None
        except:
            self.server = None
    



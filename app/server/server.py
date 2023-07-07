import socket
import logging
from time import sleep
from multiprocessing import Lock

import Pyro5.api
import Pyro5.server
import Pyro5.errors
import Pyro5.nameserver

from app.rpc.ns import *
from app.utils.utils import *
from app.utils.thread import Kthread
from app.server.worker import Worker
from app.server.dispatcher import Dispatcher


server_log = log('server', logging.INFO)


# TODO: make leader the node with smaller ip
# TODO: Differents logs
# TODO: file for configs
# TODO: change the needed try to repeat the proces n times if exception

# FIX: new coordinator and functions

@Pyro5.api.expose
class Server():
    def __init__(self, nbits: int = 8):
        # node info
        self._host = socket.gethostbyname(socket.gethostname())
        self._port = 9090
        self._id = hash(nbits, self._host)
        self._nbits = nbits
        server_log.info('Node name: {}'.format(self.node_name))

        # node state
        self._alive = True
        self._timeout = read_config()["elections_timeout"]
        self.elections_thread: Kthread = None
        self._coordinator: Server = None

        # node functions
        self._server = None
        self._root = None

        # locks
        self.lock_elections = Lock()
    
    def ping(self):
        return PING

    @property
    def id(self):
        '''
        Return the node id.
        '''
        return self._id

    @property
    def host(self):
        '''
        Return the node host.
        '''
        return self._host

    @property
    def port(self):
        '''
        Return the node port.
        '''
        return self._port

    @property
    def coordinator(self):
        '''
        Return the node coordinator.
        '''
        return self._coordinator

    @property
    def timeout(self):
        '''
        Return the node timeout.
        '''
        return self._timeout

    @property
    def node_name(self):
        '''
        Return the node name.
        '''
        return 'node-{}'.format(str(self.id))

    @property
    def worker_name(self):
        '''
        Return the worker name.
        '''
        return 'worker-{}'.format(str(self.id))

    @property
    def is_alive(self):
        '''
        Return if the node is alive.
        '''
        return self._alive

    def run(self):
        '''
        Run the node.
        '''
        self.elections_thread = Kthread(
            target=self.run_elections,
            daemon=True
        )
        self.elections_thread.start()

        while True:
            ...

    def become_leader(self):
        '''
        Become the leader.
        '''
        self.kill()
        self._server = Leader(self.host, self.port)
        self._root = Dispatcher()
        self._server.register('leader', self)
        self._server.register('request', self._root)
        self._server.register('db', self._root.db)
        server_log.info('Node: {} become leader'.format(self.node_name))

    def become_node(self):
        '''
        Become a node.
        '''
        self.kill()
        self._server = Node(self.host, self.port)
        self._root = Worker(self.host, self.port, self.id)
        self._server.register(self.worker_name, self._root, str(self.id))
        self._root.register_worker()
        server_log.info('Node: {} become worker\n'.format(self.node_name))

    ########### ELECTIONS ###########

    # TODO: Try if ns if alive, in other case call locate_ns
    def run_elections(self):
        '''
        Run the elections loop.
        '''
        while True:
            try:
                # if there is no coordinator or the coordinator is dead
                if not self.coordinator or not self.coordinator.is_alive:
                    self.election()
                
                # if the coordinator is alive
                else:
                    # compare the node coordinator with the real coordinator
                    ns = locate_ns()
                    if ns._pyroUri.host != self.coordinator.host:
                        self.election()
            
            except Pyro5.errors.PyroError:
                # coordinator is dead
                self.election()

            sleep(self.timeout)

    def find_coordinator(self):
        '''
        Find the coordinator.
        '''
        try:
            # if there is no coordinator or the coordinator is dead
            if not self.coordinator or not self.coordinator.is_alive:
                try:
                    ns = locate_ns()
                    coordinator = connect(ns, 'leader')
                    return coordinator
                except Pyro5.errors.PyroError:
                    return self
            
            # if the coordinator is alive
            else:
                try:
                    # compare the node coordinator with the real coordinator
                    ns = locate_ns()
                    if ns and ns._pyroUri.host != self.coordinator.host:
                        coordinator = connect(ns, 'leader')
                        return coordinator
                except Pyro5.errors.PyroError:
                    return self._coordinator

        except Pyro5.errors.PyroError:
            # coordinator is dead
            try:
                ns = locate_ns()
                coordinator = connect(ns, 'leader')
                return coordinator
            
            except Pyro5.errors.PyroError:
                # there is no coordinator
                return self

    def election(self):
        '''
        Go elections.
        '''

        # find the coordinator
        coordinator = self.find_coordinator()
        self._coordinator = coordinator

        # assign the functions
        try:
            if self._coordinator.id == self.id:
                if not (self._root is Leader):
                    self.become_leader()
            else:
                if not (self._root is Worker):
                    self.become_node()

        except Pyro5.errors.PyroError:
            self.election()

    def kill(self):
        '''
        kill server.
        '''
        try:
            self._server.kill_daemon()
            self._server.kill_threads()
            self._server = None
            self._root.kill_threads()
            self._root = None
        except AttributeError:
            pass    

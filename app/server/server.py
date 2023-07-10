import socket
import logging
from time import sleep
from multiprocessing import Lock
from typing import Tuple, List, Dict

import Pyro5.api
import Pyro5.server
import Pyro5.errors
import Pyro5.nameserver

from app.rpc.ns import *
from app.utils.utils import *
from app.utils.thread import Kthread
from app.server.worker import Worker
from app.server.dispatcher import Dispatcher


server_log = log('server', logging.DEBUG)


# TODO: Differents logs

# TODO: register all again

@Pyro5.api.expose
class Server():
    def __init__(self, server: str, nbits: int = 8,):
        # node info
        self._host = socket.gethostbyname(socket.gethostname())
        self._port = 9090
        self._id = hash(nbits, self._host)
        self._nbits = nbits
        server_log.info('Node name: {}'.format(self.node_name))

        # configs
        configs = read_configs()['global']
        
        # node state
        self._alive = True
        self._timeout = configs['timeout']
        self.elections_thread: Kthread = None
        self._coordinator: Server = None
        
        # successor
        succ_id = hash(nbits, server)
        self._succ = [(f'worker-{succ_id}', generate_worker_uri(succ_id, server, self._port))]

        # node functions
        self._server = None
        self._root = None

        # locks
        self.lock_elections = Lock()
        self.lock_succ = Lock()
    
    def ping(self):
        return PING

    # INFO
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
    def timeout(self):
        '''
        Return the node timeout.
        '''
        return self._timeout


    # NAMES
    @property
    def worker(self):
        '''
        Return the worker info.
        (Worker name, worker uri).
        '''
        return (self.worker_name, self.worker_uri)
    
    @property
    def worker_uri(self):
        '''
        Return the worker uri.
        '''
        return generate_worker_uri(self.id, self.host, self.port)
    
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
    

    # COORDINATOR
    @property
    def coordinator(self):
        return self._coordinator
    
    @coordinator.setter
    def coordinator(self, coordinator):
        self._coordinator = coordinator
    

    # SUCCESSION
    @property
    def succ(self):
        with self.lock_succ:
            return self._succ
    
    @succ.setter
    def succ(self, succ: List[Tuple]):
        with self.lock_succ:
            self._succ = succ
    
    def set_succ(self, succ):
        with self.lock_succ:
            self._succ.append(succ)
    
    def pop_succ(self):
        with self.lock_succ:
            if self._succ:
                self._succ.pop(0)
    

    # REGISTER IN SERVER 
    def register(self, name: str, f, id: str=None):
        self._server.register(name, f, id)
    
    def unregister(self, name: str):
        self._server.unregister(name)


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
        self.register('leader', self)
        self.register('request', self._root)
        server_log.info('Node: {} become leader'.format(self.node_name))

    def become_node(self):
        '''
        Become a node.
        '''
        self.kill()
        self._server = Node(self.host, self.port)
        self._root = Worker(self.host, self.port, self.id, self)
        server_log.info('Node: {} become worker\n'.format(self.node_name))

    ########### ELECTIONS ###########

    # TODO: Try if ns if alive, in other case call locate_ns
    def run_elections(self):
        '''
        Run the elections loop.
        '''
        while True:
            try:
                ns = locate_ns()
                if not self.coordinator or ns._pyroUri.host != self.coordinator.host:
                    self.election()
            except Pyro5.errors.PyroError:
                self.election()
            
            sleep(self.timeout)

    def election(self):
        '''
        Go elections.
        '''
        try:
            server_log.debug('find leader by ns...')
            ns = locate_ns()
            coordinator = connect(ns, 'leader')
            coordinator.ping()
            coordinator.set_succ(self.worker)
            self.succ = coordinator.succ
            self.coordinator = coordinator
            if not isinstance(self._root, Worker):
                self.become_node()
            else:
                self._root.register()
        
        except Pyro5.errors.PyroError:
            if self.succ[0] == self.worker:
                server_log.debug('node is succ...')
                self.coordinator = self
                self.succ = []
                self.become_leader()
            else:
                try:
                    server_log.debug(f'wait for succ {self.succ[0][0]} to become leader...')
                    s = direct_connect(self.succ[0][1])
                    s.ping()
                except Pyro5.errors.PyroError:
                    server_log.debug(f'dead succ {self.succ[0][0]}...')
                    self.pop_succ()
    

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

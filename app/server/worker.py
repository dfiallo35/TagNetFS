import Pyro5.api
import Pyro5.errors
import random
from time import sleep
from multiprocessing import Lock
from typing import Tuple, List, Dict

from app.database.api import *
from app.database.crud import *
from app.database.tools import *
from app.utils.constant import *
from app.utils.utils import *
from app.utils.thread import Kthread
from app.utils.utils import *
from app.rpc.ns import *
from app.server.base_server import BaseServer


worker_log = log('worker', logging.DEBUG)


# FIX: Missing data. TEST

# TODO: rollback if brake connection or separated commit?
# TODO: what happend with incomplete data?

@Pyro5.api.expose
class Worker(BaseServer):
    def __init__(self, host: str, port: int, id: int, server):
        # worker info
        self.host = host
        self.port = port
        self.id = id
        self.server = server
        
        # names
        self._worker_uri = generate_worker_uri(self.id, self.host, self.port)
        self._worker_name = f'worker-{id}'
        self._master_name = f'master-{id}'

        # database
        self.database = DatabaseSession()
        self._requests = {}
        self.results: Dict[int, dict] = {}
        self._timeout=read_config()["global_timeout"]
        self.groups_len = read_config()["groups_len"]
        self._job_id = 0
        self._succ = []

        # master-slave data
        self._group = None
        self._master = None
        self._slaves = []
        self._background_thread: Kthread = None

        # locks
        self.lock_clock = Lock()
        self.lock_working = Lock()
        self.lock_master = Lock()
        self.lock_slaves = Lock()
        self.lock_requests = Lock()
        self.lock_succ = Lock()

        # register
        self.ns_host = None
        self.register()
        self.run_worker()


    # STATUS
    def ping(self):
        return PING
    
    @property
    def master_status(self):
        '''
        Return the status of the worker.
        '''
        slaves_status = []
        for slave in self.slaves:
            try:
                s = direct_connect(slave[1])
                slaves_status.append((slave, s.slave_status))
            except Pyro5.errors.PyroError:
                pass
        status = {
            'clock': self.clock,
            'group': self.group,
            'succ': [s[0] for s in self.succ],
            'slaves': slaves_status,
        }
        return status

    @property
    def slave_status(self):
        status = {
            'clock': self.clock,
            'succ': [s[0] for s in self.succ],
        }
        return status
    
    @property
    def general_status(self):
        workers = self.masters
        print('--------------------------------------------------')
        for worker in workers:
            w = direct_connect(worker[1])
            print(worker[0])
            status: dict = w.master_status
            for i in status.keys():
                if i == 'slaves':
                    print(f'  slaves:')
                    for name, slave in status[i]:
                        print(f'     {name[0]}')
                        for s in slave.keys():
                            print(f'       {s}: {slave[s]}')
                else:
                    print(f'  {i}: {status[i]}')
            print()
        print('--------------------------------------------------')
    

    # WORKER NAMES
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
        return self._worker_uri
    
    @property
    def worker_name(self):
        return self._worker_name
    
    @property
    def master_name(self):
        return self._master_name
    
    
    # CLOCK
    @property
    def clock(self):
        '''
        Return the clock of the worker.
        '''
        with self.lock_clock:
            return self._job_id

    @clock.setter
    def clock(self, clock: int):
        '''
        Set the clock of the worker.
        '''
        with self.lock_clock:
            self._job_id = clock
    
    @property
    def timeout(self):
        return self._timeout
    

    # MASTER
    @property
    def master(self):
        '''
        Return the master.
        '''
        with self.lock_master:
            return self._master

    @master.setter
    def master(self, master: Tuple):
        '''
        Set the master.
        '''
        with self.lock_master:
            self._master = master
    
    @property
    def masters(self):
        '''
        Get the list of masters.
        '''
        timeout = self._timeout
        while True:
            try:
                ns = locate_ns()
                masters = list(ns.list(prefix='master-').items())
                alive_masters = []
                for master in masters:
                    try:
                        m = direct_connect(master[1])
                        m.ping()
                        name = master[0].split('-')[1]
                        alive_masters.append((f'worker-{name}', master[1]))
                    except:
                        pass
                return alive_masters
            except Pyro5.errors.NamingError:
                sleep(timeout)
                timeout = increse_timeout(timeout)
    
    def register_master(self):
        '''
        Register master in NS.
        '''
        self.server.register(self.master_name, self)

    def unregister_master(self):
        '''
        Unregister master from NS.
        '''
        self.server.unregister(self.master_name)
    
    def register(self):
        if self.master == self.worker:
            self.register_master()
        self.server.register(self.worker_name, self, str(self.id))
        self.ns_host = locate_ns()._pyroUri.host
    
    def ping_master(self, ):
        while True:
            try:
                ns = locate_ns()
                if self.ns_host != ns._pyroUri.host:
                    pass
                else:
                    for _ in range(3):
                        try:
                            m = direct_connect(self.master[1])
                            m.ping()
                            return True
                        except Pyro5.errors.PyroError:
                            sleep(self.timeout)
                    return False
            except Pyro5.errors.NamingError:
                pass
            sleep(self.timeout)
        
    

    # SUCCESSION
    @property
    def succ(self):
        with self.lock_succ:
            if self.master == self.worker:
                return self._slaves
            else:
                return self._succ
    
    @succ.setter
    def succ(self, succs):
        with self.lock_succ:
            self._succ = succs
    
    def pop_succ(self):
        with self.lock_succ:
            if self._succ:
                self._succ.pop(0)
    
    def update_succ(self):
        slaves = self.slaves
        for slave in slaves:
            try:
                s = direct_connect(slave[1])
                s.succ = slaves
            except Pyro5.errors.PyroError:
                pass

    def change_master(self, new_master: Tuple, group: int, succ: List[Tuple]):
        if self.master != new_master:
            self.kill_threads()
            self.master = new_master
            self.group = group
            self.succ = succ
            self.run_threads()
    

    # SLAVES
    @property
    def slaves(self):
        '''
        Return the slaves.
        '''
        with self.lock_slaves:
            return self._slaves

    @slaves.setter
    def slaves(self, slaves: Tuple|List[Tuple]):
        '''
        Set the slaves.
        '''
        with self.lock_slaves:
            self._slaves = slaves
    
    def set_slave(self, slave: Tuple):
        with self.lock_slaves:
            if slave not in self._slaves:
                self._slaves.append(slave)
    
    def pop_slave(self, slave: Tuple):
        with self.lock_slaves:
            if slave in self._slaves:
                return self._slaves.pop(self._slaves.index(slave))
    

    # GROUP
    @property
    def group(self):
        '''
        Return the group.
        '''
        return self._group

    @group.setter
    def group(self, group: int):
        '''
        Set the group.
        '''
        self._group = group
    

    # REQUESTS
    @property
    def requests(self):
        '''
        Return the requests.
        '''
        with self.lock_requests:
            return self._requests

    @requests.setter
    def requests(self, id_request: Tuple):
        '''
        Set the requests.
        '''
        with self.lock_requests:
            id, request = id_request
            self._requests[id] = request
    

    def data_from_masters(self):
        # get data from masters
        masters = self.masters
        master_group = {}
        master_len = []
        for master in masters:
            try:
                m = direct_connect(master[1])
                slaves = m.slaves
                master_group[master] = m.group
                master_len.append((master, len(slaves)+1))
            except Pyro5.errors.PyroError:
                pass
        
        # set new group number
        new_group = 1
        for i, g in enumerate(sorted(list(master_group.values()))):
            i+=1
            if i != g:
                new_group = i
                break
            else:
                new_group = i+1
        
        master_len = sorted(master_len, key=lambda x: x[1])

        return new_group, master_len
    
    def update_worker(self, master: Tuple, group: Tuple, slave: Tuple=None):
        self.master = master
        self.group = group
        if slave:
            self.set_slave(slave)

    def run_worker(self):
        '''
        Register the worker to the name server and the database.
        '''
        while not self.group:
            try:
                worker_log.info('register node...')
                new_group, master_len = self.data_from_masters()
                self.clear_db()

                # if worker has no group
                if not self.group:
                    if master_len:
                        first_group = master_len[0]
                        last_group = master_len[-1]

                        # if there is a group with less workers than groups_len
                        if first_group[1] < self.groups_len:
                            worker_log.debug('less workers than groups_len...')
                            master = first_group[0]
                            m = direct_connect(master[1])
                            self.update_worker(master, m.group)
                            m.set_slave(self.worker)
                            m.update_succ()
                        
                        # if there is a group with more workers than groups_len
                        elif last_group[1] > self.groups_len:
                            worker_log.debug('more workers than groups_len...')
                            # TODO: clear db
                            m = direct_connect(last_group[0][1])
                            new_slave = m.pop_slave(m.slaves[-1])
                            self.update_worker(self.worker, new_group, new_slave)
                            s = direct_connect(new_slave[1])
                            s.change_master(self.worker, new_group, self.slaves)
                            self.register_master()
                            m.update_succ()

                        # if all the groups have the correct number of workers
                        else:
                            worker_log.debug('all the groups have groups_len...')
                            master = first_group[0]
                            m = direct_connect(master[1])
                            self.update_worker(master, m.group)
                            m.set_slave(self.worker)
                            m.update_succ()
                    
                    # if there is no groups
                    else:
                        worker_log.debug('no groups...')
                        self.update_worker(self.worker, new_group)
                        self.register_master()
                
                self.run_threads()
                self.general_status
            except Pyro5.errors.PyroError:
                sleep(self._timeout)
    
    
    def regroup(self):
        '''
        Regroup the worker to a group.
        '''
        worker_log.info('regroup...')
        new_group, master_len = self.data_from_masters()
        
        # if master
        if self.master == self.worker:
            if not self.slaves:
                master_len = sorted([_m for _m in master_len if _m[0][0] != self.worker_name], key=lambda x: x[1])

                if master_len:
                    first_group = master_len[0]
                    last_group = master_len[-1]
                    master = first_group[0]
                    
                    if first_group[1] < self.groups_len:
                        worker_log.debug('less workers than groups_len...')  
                        self.replicate_to_masters()
                        m = direct_connect(master[1])
                        self.update_worker(master, m.group)
                        self.unregister_master()
                        m.set_slave(self.worker)
                        m.update_succ()
                    
                    elif last_group[1] > self.groups_len:
                        worker_log.debug('more workers than groups_len...')
                        m = direct_connect(last_group[0][1])
                        new_slave = m.pop_slave(m.slaves[-1])
                        self.update_worker(self.worker, new_group, new_slave)
                        s = direct_connect(new_slave[1])
                        s.change_master(self.worker, new_group, self.slaves)
                        self.unregister_master()
                        self.register_master()
                        m.update_succ()
                    
                    else:
                        worker_log.debug('all the groups have groups_len...')
                        self.replicate_to_masters()
                        m = direct_connect(master[1])
                        self.update_worker(master, m.group)
                        self.unregister_master()
                        m.set_slave(self.worker)
                        m.update_succ()

        # if not master    
        else:
            # if there is successor
            if self.succ:
                succ = self.succ[0]

                # if there is only one succ
                if len(self.succ) == 1:
                    worker_log.debug('there is only one succ...')
                    
                    # exist masters
                    if master_len:
                        worker_log.debug('exist masters...')
                        first_group = master_len[0]
                        last_group = master_len[-1]
                        master = first_group[0]
                        
                        if first_group[1] < self.groups_len:
                            worker_log.debug('less workers than groups_len...')  
                            self.replicate_to_masters()
                            m = direct_connect(master[1])
                            self.update_worker(master, m.group)
                            m.set_slave(self.worker)
                            m.update_succ()
                        
                        elif last_group[1] > self.groups_len:
                            worker_log.debug('more workers than groups_len...')
                            m = direct_connect(last_group[0][1])
                            new_slave = m.pop_slave(m.slaves[-1])
                            self.update_worker(self.worker, new_group, new_slave)
                            s = direct_connect(new_slave[1])
                            s.change_master(self.worker, new_group, self.slaves)
                            self.register_master()
                            m.update_succ()
                        
                        else:
                            worker_log.debug('all the groups have groups_len...')
                            self.replicate_to_masters()
                            m = direct_connect(master[1])
                            self.update_worker(master, m.group)
                            m.set_slave(self.worker)
                            self.succ = m.succ
                            m.update_succ()
                    
                    # not exist masters
                    else:
                        worker_log.debug('not exist masters...')
                        self.master = self.worker
                        self.register_master()
                        self.succ = []
                
                # FIX: for successors
                # if worker is the successor
                elif self.worker == succ:
                    worker_log.debug('worker is succ...')
                    self.master = self.worker
                    self.register_master()
                    self.succ = []
                
                # if there is a successor but not this worker
                else:
                    worker_log.debug('worker is not succ...')
                    try:
                        m = direct_connect(succ[1])
                        if m.master == succ:
                            self.master = succ
                            m.set_slave(self.worker)
                            self.succ = m.succ
                    except Pyro5.errors.PyroError:
                        worker_log.debug('succ is not conected, next succ...')
                        self.pop_succ()
                
            # if there is no successor
            else:
                worker_log.debug('there is not succ')
                self.master = self.worker
                self.register_master()
                self.succ = []
        
        self.general_status


    # THREADS
    def background(self):
        '''
        Background thread.
        '''
        while True:
            
            # if the worker is not the master, ping the master
            if self.master != self.worker:
                if not self.ping_master():
                    worker_log.info('no master, regroup')
                    self.regroup()
            
            # if the worker is the master, try replicating
            else:
                self.replicate()
            sleep(self._timeout)
    
    def run_threads(self):
        '''
        Run the background thread.
        '''
        self._background_thread = Kthread(
            target=self.background,
            daemon=True
        )
        self._background_thread.start()
    
    def kill_threads(self):
        '''
        Kill the background thread.
        '''
        try:
            self._background_thread.kill()
            self._background_thread = None
        except:
            self._background_thread = None


    # DATABASE
    def get_result(self, id: int):
        '''
        Return the result of the request.
        '''
        with self.lock_working:
            if self.results.get(id) is not None:
                return self.results.pop(id)
            return None

    def get_db(self):
        '''
        Return the database.
        '''
        return self.database.get_db()

    def export_db(self, n: int):
        '''
        Export the database dividing it in n parts.
        '''
        with self.lock_working:
            worker_log.info('export db...\n')
            return divide_db(self.get_db(), n)
        

    def import_db(self, files, clock: int=None):
        '''
        Import the database and set the clock.
        '''
        with self.lock_working:
            worker_log.info('import files...\n')
            save_files(self.get_db(), files)
            with self.lock_requests:
                self._requests = {}
            if not clock:
                self.clock += 1
            else:
                self.clock = clock

    def clear_db(self):
        '''
        Clear the database.
        '''
        with self.lock_working:
            worker_log.info('clear db...\n')
            clear_db(self.get_db())
            self.clock = 0

    def locate_file(self, file_name: str):
        '''
        Return True if the file is in the database.
        '''
        with self.lock_working:
            print('locate...\n')
            file = get_files_by_name(self.get_db(), file_name)
            if file:
                return True
            return False

    def run(self, request: Tuple, id: int):
        '''
        Run the request.
        '''
        self.clock = self.clock + 1
        self.requests = (self.clock, request)
        t = Kthread(
            target=self.execute,
            args=(request, id),
            daemon=True,
        )
        t.start()

    def execute(self, request: Tuple, id: int):
        '''
        Execute the request.
        '''
        with self.lock_working:
            match request[0]:
                case 'add':
                    worker_log.info('add executed...\n')
                    self.results[id] = add(dirs_to_UploadFile(
                        request[1]), request[2], self.get_db())
                case 'delete':
                    worker_log.info('delete executed...\n')
                    self.results[id] = delete(request[1], self.get_db())
                case 'list':
                    worker_log.info('list executed...\n')
                    self.results[id] = qlist(request[1], self.get_db())
                case 'add-tags':
                    worker_log.info('add-tags executed...\n')
                    self.results[id] = add_tags(
                        request[1], request[2], self.get_db())
                case 'delete-tags':
                    worker_log.info('delete-tags executed...\n')
                    self.results[id] = delete_tags(
                        request[1], request[2], self.get_db())
                case _:
                    worker_log.info('Not job implemented\n')
    

    # REPLICATION
    def replicate_to_masters(self):
        completed = False
        while not completed:
            try:
                masters = self.masters
                files = self.export_db(len(masters))
                for master, f in zip(masters, files):
                    m = direct_connect(master[1])
                    m.import_db(f)
                self.clear_db()
                completed = True
            except Pyro5.errors.PyroError:
                pass

    # FIX
    def replicate(self):
        '''
        Replicate the database to the slaves.
        '''
        for slave in self.slaves:
            try:
                # try to connect to the slave
                w = direct_connect(slave[1])
                w_clock = w.clock
                next_clock = w_clock+1

                # if the slave's clock is behind the master's clock
                if w_clock < self.clock:
                    # if next request to slave is in requests
                    if next_clock in self.requests:
                        # request that modify the db, all except LIST
                        if self.requests[next_clock][0] != LIST:
                            worker_log.debug(f'replicate: run {self.requests[next_clock][0]}\n')
                            w.run(self.requests[next_clock], next_clock)

                            # Wait responce
                            timeout = self._timeout
                            while True:
                                r = w.get_result(next_clock)
                                if r is not None:
                                    break
                                else:
                                    sleep(self._timeout)
                                    timeout = increse_timeout(timeout)
                        
                        # just update for requests that don't modify the db, LIST request
                        else:
                            worker_log.info(f'replicate: set clock\n')
                            w.clock = next_clock
                    else:
                        # copy all the db to the slave
                        # FIX: delete the database of the slave before export
                        worker_log.info(f'replicate: Copy all db to {slave[0]}...')
                        files = self.export_db(1)[0]
                        w.clear_db()
                        w.import_db(files, self.clock)
                        worker_log.info(f'replicate: end copy to {slave[0]}\n')
            
            except Pyro5.errors.PyroError:
                # if the slave is not reachable
                worker_log.info(f'replicate: slave: {slave[0]} disconected')
                self.pop_slave(slave)
                self.update_succ()
                self.regroup()

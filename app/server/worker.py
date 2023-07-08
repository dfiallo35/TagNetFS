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


worker_log = log('worker', logging.INFO)


# FIX: different id than db class
# TODO: si se cambia el clock pero no se ha copiado la db que pasa en la replicacion

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
        self.worker_name = f'worker-{id}'
        self.node_name = f'node-{id}'
        self.master_name = f'master-{id}'

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

    def ping(self):
        return PING

    @property
    def status(self):
        '''
        Return the status of the worker.
        '''
        status = {
            'clock': self.clock,
            'group': self.group,
            'master': self.master[0],
            'slaves': [s[0] for s in self.slaves],
        }
        return status
        # print('--------------------------------------------------')
        # print(self.worker_name)
        # print(f'  clock: {self.clock}')
        # print(f'  group: {self.group}')
        # print(f'  master: {self.master[0]}')
        # print(f'  slaves: {[s[0] for s in self.slaves]}')
        # print('--------------------------------------------------')
    
    def master_status(self):
        workers = self.masters
        print('--------------------------------------------------')
        for worker in workers:
            w = direct_connect(worker[1])
            print(worker[0])
            status: dict = w.status
            for i in status.keys():
                print(f'  {i}: {status[i]}')
            print()
        print('--------------------------------------------------')
    
    @property
    def worker(self):
        '''
        Return the worker info.
        '''
        return (self.worker_name, self.worker_uri)

    @property
    def worker_uri(self):
        '''
        Return the worker uri.
        '''
        return self._worker_uri
    
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
    
    def get_succ(self):
        return self.slaves
        # slaves = self.slaves
        # order = [s for s,_ in sorted([(slave, get_ip_from_uri(slave[1])) for slave in slaves], key=lambda x: x[1])]
        # return order
    

    def change_master(self, new_master: Tuple, group: int, succ: List[Tuple]):
        if self.master != new_master:
            self.kill_threads()
            self.master = new_master
            self.group = group
            self.succ = succ
            self.run_threads()
    
    def succeed_master(self):
        ...

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
    
    def own_slave(self, slave: Tuple):
        '''
        Return True if the slave is owned by the worker.
        '''
        try:
            s = direct_connect(slave[1])
            if s.group == self.group:
                return True
            else:
                return False
        except Pyro5.errors.PyroError:
            return False

    @property
    def group(self):
        '''
        Return the group.
        '''
        return self._group

    # TODO: notify master the group change
    @group.setter
    def group(self, group: int):
        '''
        Set the group.
        '''
        self._group = group
    
    @property
    def masters(self):
        '''
        Get the list of masters.
        '''
        timeout = self._timeout
        while True:
            try:
                ns = locate_ns()
                return list(ns.list(prefix='master-').items())
            except Pyro5.errors.NamingError:
                sleep(timeout)
                timeout = increse_timeout(timeout)

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
    
    def register_worker(self):
        '''
        Register the worker to the name server and the database.
        '''
        while not self.group:
            try:
                worker_log.info('register node...')
                self.regroup()
                ...
                self.clear_db()
                self.run_threads()
            except Pyro5.errors.PyroError:
                sleep(self._timeout)
    
    def register_master(self):
        done = False
        while not done:
            try:
                self.server.register(self.master_name, self)
                done = True
            except:
                pass
    
    def unregister_master(self):
        # TODO: unregister master
        ...
    
    def run_threads(self):
        '''
        Run the background thread.
        '''
        self._background_thread = Kthread(
            target=self.background,
            daemon=True
        )
        self._background_thread.start()

    # TODO: kill and recreate threads?
    # TODO: send succ to slaves
    # TODO: clear slaves, succ, db
    def regroup(self):
        '''
        Regroup the worker to a group.
        '''
        worker_log.info('regroup...\n')

        # get data from masters
        masters = self.masters
        master_data = {}
        master_len = []
        for master in masters:
            try:
                m = direct_connect(master[1])
                slaves = m.slaves
                master_data[master] = {'slaves':slaves, 'group':m.group}
                master_len.append((master, len(slaves)+1))
            except Pyro5.errors.PyroError:
                pass
        
        # set new group number
        new_group = 1
        for i, g in enumerate(sorted([v['group'] for v in master_data.values()])):
            i+=1
            if i != g:
                new_group = i
                break
            else:
                new_group = i+1
        
        # sort masters by the number of workers in group
        master_len = sorted(master_len, key=lambda x: x[1])

        # if worker has no group
        if not self.group:
            if master_len:
                first_group = master_len[0]
                last_group = master_len[-1]

                # if there is a group with less workers than groups_len
                if first_group[1] < self.groups_len:
                    print('less workers than groups_len...')
                    master = first_group[0]
                    self.master = master
                    self.group = master_data[master]['group']
                    m = direct_connect(master[1])
                    m.set_slave(self.worker)
                    self.succ = m.succ
                
                # if there is a group with more workers than groups_len
                elif last_group[1] > self.groups_len:
                    print('more workers than groups_len...')
                    self.master = self.worker
                    self.group = new_group
                    m = direct_connect(last_group[0][1])
                    # TODO: clear db
                    # TODO: change succ
                    new_slave = m.pop_slave(random.choice(m.slaves))
                    s = direct_connect(new_slave[1])
                    self.set_slave(new_slave)
                    s.change_master(self.worker, new_group, self.slaves)
                    self.register_master()

                # if all the groups have the correct number of workers
                else:
                    print('all the groups have groups_len...')
                    master = first_group[0]
                    self.master = master
                    self.group = master_data[master]['group']
                    m = direct_connect(master[1])
                    m.set_slave(self.worker)
                    self.succ = m.succ
            
            # if there is no groups
            else:
                print('no groups...')
                self.master = self.worker
                self.group = new_group
                self.register_master()
        
        # if worker has a group
        else:
            first_group = master_len[0]
            last_group = master_len[-1]

            # if there is successor
            if self.succ:
                succ = self.succ[0]

                # if there is only one succ
                if len(self.succ) == 1:
                    print('there is only one succ...')
                    # TODO: replicate data
                    master = first_group[0]
                    self.master = master
                    self.group = master_data[master]['group']
                    m = direct_connect(master[1])
                    m.set_slave(self.worker)
                    self.succ = m.succ
                
                # if worker is the successor
                elif self.worker == succ:
                    print('worker is succ...')
                    self.master = self.worker
                    self.succ = []
                
                # if there is a successor but not this worker
                else:
                    print('worker is not succ...')
                    try:
                        m = direct_connect(succ[1])
                        if m.master == succ:
                            self.master = succ
                            m.set_slave(self.worker)
                            self.succ = m.succ
                    except Pyro5.errors.PyroError:
                        print('succ is not conected, next succ...')
                        self.pop_succ()
                
            # if there is no successor
            else:
                print('there is not succ')
                # TODO: if there is no successor
                self.master = self.worker
                self.succ = []
        
        self.master_status()
        
        # TODO: already a worker
            # TODO: lost master
            # TODO: lost slave

        # group, master, slaves = db.regroup(self.group, self.worker)
        
        # # If worker is being moved to a new group, export his db and clear it
        # if self.group and self.master == self.worker and self.group != group:
        #     worker_log.info('changing group...\n')
        #     completed = False
        #     while not completed:
        #         try:
        #             masters = [_m for _m in db.masters if _m != self.worker]
        #             files = self.export_db(len(masters))
        #             for master, f in zip(masters, files):
        #                 m = direct_connect(master[1])
        #                 m.import_db(f)
        #             self.clear_db()
        #             completed = True
        #         except Pyro5.errors.PyroError:
        #             pass

        # # update slaves
        # if master == self.worker:
        #     for slave in slaves:
        #         try:
        #             s = direct_connect(slave[1])
        #             slave_master = s.master
        #             if slave_master != master:
        #                 s.master = master
        #                 s.clock = 0
        #                 s.clear_db()
        #             s.slaves = []
        #             s.group = group
        #         except Pyro5.errors.PyroError:
        #             if slave in self.slaves:
        #                 self.slaves.remove(slave)
        # # tell the master that this is a new slave
        # else:
        #     completed = False
        #     while not completed:
        #         try:
        #             m = direct_connect(master[1])
        #             m.slaves = self.worker
        #             completed = True
        #         except Pyro5.errors.PyroError:
        #             sleep(self._timeout)

    def background(self):
        '''
        Background thread.
        '''
        while True:
            # if the worker is not the master, ping the master
            if self.master != self.worker:
                try:
                    worker_log.debug('ping master...\n')
                    m = direct_connect(self.master[1])
                    m.ping()
                except Pyro5.errors.PyroError:
                    worker_log.info('no master, regroup')
                    # TODO: what to do when there is no master
                    self.regroup()
            # if the worker is the master, try replicating
            else:
                worker_log.debug('replicate...\n')
                # self.replicate()
            sleep(self._timeout)


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
    
    def kill_threads(self):
        '''
        Kill the background thread.
        '''
        try:
            self._background_thread.kill()
            self._background_thread = None
        except:
            self._background_thread = None

    # FIX
    def replicate(self):
        '''
        Replicate the database to the slaves.
        '''
        for slave in self.slaves:
            # if this master is not the master of the slave go regroup
            if not self.own_slave(slave):
                worker_log.info(f'replicate: slave: {slave[0]} belongs to another group')
                self.regroup()
                break
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
            
            except Pyro5.errors.PyroError as e:
                # if the slave is not reachable, regroup
                worker_log.info(f'replicate: slave: {slave[0]} disconected')
                print(e)
                self.regroup()

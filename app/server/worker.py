import Pyro5.api
import Pyro5.errors
from time import sleep
from threading import Lock
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


# FIX: different id than db class

@Pyro5.api.expose
class Worker(BaseServer):
    def __init__(self, host: str, port: int, id: int):
        self.host = host
        self.port = port
        self.id = id

        self._worker_uri = generate_worker_uri(self.id, self.host, self.port)
        self.worker_name = f'worker-{id}'

        self.database = DatabaseSession()
        self._requests = {}
        self.results: Dict[int, dict] = {}
        self._timeout = 0.1

        self._group = None
        self._master = None
        self._slaves = []
        self._background_thread: Kthread = None
        
        self._job_id = 0
        self._busy = False

        # LOCKS
        self.lock_clock = Lock()
        self.lock_busy = Lock()
        self.lock_master = Lock()
        self.lock_slaves = Lock()
        self.lock_requests = Lock()

    def ping(self):
        return PING

    @property
    def status(self):
        status = {
            'clock': self.clock,
            'group': self.group,
            'master': self.master[0],
            'slaves': [s[0] for s in self.slaves],
        }
        return status
    
    @property
    def worker(self):
        return (self.worker_name, self.worker_uri)

    @property
    def worker_uri(self):
        return self._worker_uri
    

    @property
    def clock(self):
        with self.lock_clock:
            return self._job_id

    @clock.setter
    def clock(self, clock: int):
        with self.lock_clock:
            self._job_id = clock

    @property
    def master(self):
        with self.lock_master:
            return self._master

    @master.setter
    def master(self, master: Tuple):
        with self.lock_master:
            self._master = master

    @property
    def slaves(self):
        with self.lock_slaves:
            return self._slaves

    @slaves.setter
    def slaves(self, slaves: Tuple|List[Tuple]):
        with self.lock_slaves:
            if isinstance(slaves, Tuple):
                self._slaves.append(slaves)
                self._slaves = list(set(self._slaves))
            else:
                self._slaves = slaves
    
    def own_slave(self, slave: Tuple):
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
        return self._group

    @group.setter
    def group(self, group: int):
        self._group = group

    @property
    def busy(self):
        with self.lock_busy:
            return self._busy

    @busy.setter
    def busy(self, busy: bool):
        with self.lock_busy:
            self._busy = busy

    @property
    def requests(self):
        with self.lock_requests:
            return self._requests

    @requests.setter
    def requests(self, id_request: Tuple):
        with self.lock_requests:
            id, request = id_request
            self._requests[id] = request
    
    def register_worker(self):
        while not self.group:
            try:
                self.regroup()
                self._background_thread = Kthread(
                    target=self.background,
                    daemon=True
                )
                self._background_thread.start()
            except Pyro5.errors.PyroError:
                sleep(self._timeout)
    

    def regroup(self):
        ns = locate_ns()
        db = connect(ns, 'db')
        group, master, slaves = db.regroup(self.group, self.worker)
        
        # FIX: 
        # to export database when this node is sent to another group
        if self.group and self.master == self.worker and self.group != group:
            worker_log.debug('changing group\n')
            completed = False
            while not completed:
                try:
                    masters = db.masters
                    files = self.export_db(len(masters))
                    for master, f in zip(masters, files):
                        m = direct_connect(master[1])
                        m.import_db(f, self.clock)
                    self.clear_db()
                    completed = True
                except Pyro5.errors.PyroError:
                    pass
        
        # tell the slaves that this is the new master
        if master == self.worker:
            for slave in slaves:
                try:
                    s = direct_connect(slave[1])
                    s.master = master
                except Pyro5.errors.PyroError:
                    pass
        else:
            completed = False
            while not completed:
                try:
                    m = direct_connect(master[1])
                    m.slaves = self.worker
                    completed = True
                except Pyro5.errors.PyroError:
                    sleep(self._timeout)
        
        self.group = group
        self.master = master
        self.slaves = slaves
        db.workers_status()

    def background(self):
        while True:
            if self.master != self.worker:
                try:
                    worker_log.debug('ping master...\n')
                    m = direct_connect(self.master[1])
                    m.ping()
                except Pyro5.errors.PyroError:
                    worker_log.debug('no master, regroup\n')
                    self.regroup()
            else:
                worker_log.debug('replicate...\n')
                self.replicate()
            sleep(1)

    def pop_slave(self, slave: int):
        with self.lock_slaves:
            if slave in self._slaves:
                self._slaves.remove(slave)

    def get_result(self, id: int):
        if self.results.get(id) is not None:
            return self.results.pop(id)
        return None

    def get_db(self):
        return self.database.get_db()

    def export_db(self, n: int):
        worker_log.info('export db...\n')
        return divide_db(self.get_db(), n)

    def import_db(self, files, clock: int):
        worker_log.info('import files...\n')
        self.clock = clock
        save_files(self.get_db(), files)

    def clear_db(self):
        clear_db(self.get_db())

    def locate_file(self, file_name: str):
        print('locate...')
        file = get_files_by_name(self.get_db(), file_name)
        if file:
            return True
        return False

    def run(self, request: Tuple, id: int):
        self.clock = self.clock + 1
        self.requests = (self.clock, request)
        t = Kthread(
            target=self.execute,
            args=(request, id),
            daemon=True,
        )
        t.start()

    def execute(self, request: Tuple, id: int):
        self.busy = True
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
        self.busy = False
    
    def kill_threads(self):
        try:
            self._background_thread.kill()
        except:
            pass

    # FIX
    def replicate(self):
        for slave in self.slaves:
            if not self.own_slave(slave):
                self.regroup()
                break
            try:
                w = direct_connect(slave[1])
                w_clock = w.clock
                next_clock = w_clock+1
                if w_clock < self.clock:
                    if next_clock in self.requests:
                        if not w.busy:
                            if self.requests[next_clock][0] == ADD:
                                worker_log.debug(f'replicate: run add\n')
                                w.run(
                                    self.requests[next_clock], next_clock)

                                # Wait responce
                                timeout = self._timeout
                                while True:
                                    if not w.busy:
                                        r = w.get_result(next_clock)
                                        if r is not None:
                                            break
                                    else:
                                        sleep(self._timeout)
                                        timeout = increse_timeout(timeout)
                            else:
                                worker_log.debug(f'replicate: set clock\n')
                                w.clock = next_clock
                    else:
                        worker_log.info(
                            f'replicate: Copy all db to {slave[0]}...\n')
                        files = self.export_db(1)[0]
                        w.import_db(files, self.clock)
            except Pyro5.errors.PyroError:
                self.regroup()

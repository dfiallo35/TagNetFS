import Pyro5.api
import Pyro5.errors
from time import sleep
from threading import Lock
from typing import Tuple, List, Dict

from app.database.api import *
from app.database.crud import *
from app.utils.constant import *
from app.utils.utils import *
from app.utils.thread import Kthread
from app.utils.utils import *
from app.rpc.ns import *


worker_log = log('worker', logging.INFO)


# FIX: different id than db class

@Pyro5.api.expose
class Worker():
    def __init__(self):
        self.database = DatabaseSession()
        self._requests = {}
        self.results: Dict[int, dict] = {}
        self._timeout = 0.1

        self._group = None
        self._master = False
        self._slaves = []
        self._replicate: Kthread = None

        self._job_id = 0
        self._busy = False

        # LOCKS
        self.lock_clock = Lock()
        self.lock_busy = Lock()
        self.lock_slaves = Lock()
        self.lock_requests = Lock()

    @property
    def status(self):
        status = {
            'clock': self.clock,
            'group': self.group,
            'master': self.master,
            'slaves': [s[0] for s in self.slaves],
        }
        return status

    def ping(self):
        return PING

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
        return self._master

    # FIX
    @master.setter
    def master(self, master: bool):
        if master:
            self._replicate = Kthread(
                target=self.replicate,
                daemon=True
            )
            self._replicate.start()
        else:
            if self._replicate:
                self._replicate.kill()
        self._master = master

    @property
    def slaves(self):
        with self.lock_slaves:
            return self._slaves

    @slaves.setter
    def slaves(self, slaves: List[Tuple]):
        with self.lock_slaves:
            self._slaves = slaves

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

    def get_result(self, id: int):
        if self.results.get(id) is not None:
            return self.results.pop(id)
        return None

    def get_db(self):
        return self.database.get_db()

    def export_db(self, n: int):
        worker_log.info('export db...\n')
        return divide_db(self.get_db(), n)

    def import_db(self, files):
        worker_log.info('import files...\n')
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

    # TODO: disconected nodes

    def replicate(self):
        while True:
            for slave in self.slaves:
                try:
                    w = direct_connect(slave[1])
                    w_clock = w.clock
                    next_clock = w_clock+1
                    if w_clock < self.clock:
                        if next_clock in self.requests:
                            if not w.busy:
                                if self.requests[next_clock][0] == ADD:
                                    print(f'replicate: run add\n')
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
                                    print(f'replicate: set clock\n')
                                    w.clock = next_clock
                        else:
                            worker_log.info(
                                f'replicate: Copy all db to {slave[0]}...\n')
                            files = self.export_db(1)[0]
                            w.import_db(files)
                except Pyro5.errors.PyroError:
                    pass
            sleep(self._timeout)

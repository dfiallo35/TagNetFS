import random
from time import sleep
from multiprocessing import Lock
from typing import Tuple, List, Dict

import Pyro5.api
import Pyro5.errors

from app.rpc.ns import *
from app.utils.utils import *
from app.utils.constant import *
from app.utils.thread import Kthread
from app.server.base_server import BaseServer


db_log = log('dispatcher', logging.INFO)


# TODO: if dont get responce from server, repeat the requets to other server from the same group


@Pyro5.api.expose
class Dispatcher(BaseServer):
    def __init__(self):
        # db state
        self._job_id = 0
        self._requests: Dict[int, Tuple] = {}
        self.results: Dict[int, List[dict]] = {}

        # configs
        configs = read_configs()['global']
        self._timeout = configs['timeout']

        # locks
        self.lock_id = Lock()

    def ping(self):
        return PING


    # CLOCK
    @property
    def clock(self):
        with self.lock_id:
            return self._job_id

    @clock.setter
    def clock(self, id: int):
        with self.lock_id:
            self._job_id = id

    @property
    def timeout(self):
        return self._timeout
    

    # MASTERS
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
                        alive_masters.append(master)
                    except:
                        pass
                return alive_masters
            except Pyro5.errors.NamingError:
                sleep(timeout)
                timeout = increse_timeout(timeout)


    # REQUESTS
    def request(self, request: Tuple):
        results = self.execute(request)
        return results
    
    # FIX: TRY
    def execute(self, request: Tuple):
        id = self.clock + 1
        self.clock = id
        timeout = self.timeout
        while True:
            try:
                requests = self.assign_workers(request)
                self.add_request(requests, id)
                self.assign_jobs(requests, id)
                self.get_results(requests, id)
                result = self.merge_results(self.results[id])
                return result
            except Pyro5.errors.PyroError:
                sleep(timeout)
                timeout = increse_timeout(timeout)

    # FIX
    def add_request(self, requests: Tuple, id: int):
        self._requests[id] = requests    

    def locate_file(self, workers: List[Tuple], file_name: str):
        '''
        Locate the file in the db.
        '''
        db_log.debug('execute: locate file...')
        for worker in workers:
            w = direct_connect(worker[1])
            located_file = w.locate_file(file_name)

            if located_file:
                return worker
        return None

    def assign_workers(self, request: Tuple):
        '''
        Select workers that should do the next job.
        '''
        db_log.debug('excecute: assign_workers...')
        workers = self.masters
        if request[0] == ADD:
            rewrite: Dict[Tuple, List] = {}
            add = []
            for f in request[1]:
                worker = self.locate_file(workers, f[1])
                if worker:
                    if not rewrite.get(worker):
                        rewrite[worker] = [f]
                    else:
                        rewrite[worker].append(f)
                else:
                    add.append(f)

            if add:
                w = random.choice(workers)
                if w in rewrite:
                    rewrite[w].extend(add.copy())
                    add = []
                else:
                    add = [([w], (request[0], [f for f in add], request[2]))]
            requests = [([w], (request[0], [f for f in j], request[2]))
                        for w, j in zip(rewrite.keys(), rewrite.values())]
            if add:
                requests.extend(add)
            return requests
        else:
            return [(workers, request)]

    # TODO: TRY
    def assign_jobs(self, requests: List[Tuple], id: int):
        '''
        Send the request to the workers.
        '''
        db_log.debug('excecute: assign_jobs...')
        timeout = self.timeout
        for workers, request in requests:
            for worker in workers:
                w = direct_connect(worker[1])
                db_log.info(
                    f'assing jobs: send work to {worker[0]}...\n')
                w.run(request, id)

    # TODO: TRY
    # TODO: What to do with the losed request results
    def get_results(self, requests: List[Tuple], id: int):
        '''
        Wait for the results.
        '''
        db_log.debug('excecute: get_results...')
        timeout = self.timeout
        self.results[id] = []
        for workers, _ in requests:
            for worker in workers:
                db_log.info(f'get results: wait responce from {worker[0]}...')
                try:
                    w = direct_connect(worker[1])
                    while True:
                        r = w.get_result(id)
                        if r is not None:
                            db_log.info(f'results: {r}\n')
                            self.results[id].append(r)
                            break
                        else:
                            sleep(self.timeout)
                            timeout = increse_timeout(timeout)
                except Pyro5.errors.PyroError:
                    pass

    def merge_results(self, results: List[dict]):
        '''
        Merge all the results given by the workers.
        '''
        db_log.debug('excecute: results...')
        if results and results[0] and list(results[0].keys())[0] == 'messagge':
            return {'messagge': 'correct'}
        else:
            r = {}
            for i in results:
                r.update(i)
            return r

    def kill_threads(self):
        ...
import random
# import pandas as pd
from math import ceil
from time import sleep
from threading import Lock
from typing import Tuple, List, Dict

from app.rpc.ns import *
from app.utils.utils import *
from app.utils.constant import *
from app.utils.thread import Kthread

db_log = log('data-base', logging.INFO)


# FIX: list before add
# TODO: if dont get responce from server, repeat the requets to other server from the same group


class DataBase:
    def __init__(self) -> None:
        self._job_id = 0
        self.worker_prefix = 'worker-'
        self._timeout = 0.1
        self._requests: Dict[int, Tuple] = {}
        self.results: Dict[int, List[dict]] = {}
        
        # GROUPS
        self._groups_len = 2
        self._timeout_groups = 2
        self._groups: Dict[int, Dict[str, List|Tuple]] = {}
        self._assign_froups = Kthread(
            target=self.assign_groups,
            daemon=True,
        )
        self._assign_froups.start()

        # LOCKS
        self.lock_id = Lock()
        self.lock_groups = Lock()

    @property
    def job_id(self):
        with self.lock_id:
            return self._job_id
    
    @job_id.setter
    def job_id(self, id: int):
        with self.lock_id:
            self._job_id = id
    
    @property
    def timeout(self):
        return self._timeout
    
    @property
    def groups(self):
        with self.lock_groups:
            return self._groups
    
    @groups.setter
    def groups(self, groups: Dict):
        with self.lock_groups:
            self._groups = groups
    
    # FIX: TRY
    def execute(self, request: Tuple):
        id = self.job_id + 1
        self.job_id = id
        self.add_request(request, id)

        timeout = self.timeout
        while True:
            try:
                workers = self.assign_workers(request)
                self.add_request_workers(id, workers)
                self.assign_jobs(workers, request, id)
                self.get_results(workers, id)
                result = self.merge_results(self.results[id])
                return result
            except Pyro5.errors.PyroError:
                sleep(timeout)
                timeout = increse_timeout(timeout)

    def add_request(self, request: Tuple, id: int):
        self._requests[id] = {'request':request, 'workers': []}
    
    def add_request_workers(self, id: int, workers: List):
        db_log.debug('excecute: add_request_workers...')
        if self._requests.get(id):
            self._requests[id]['workers'] = workers.copy()
    
    def workers(self):
        '''
        Get the list of all availble workers.
        '''
        timeout = self.timeout
        while True:
            try:
                ns = locate_ns()
                return list(ns.list(prefix=self.worker_prefix).items())
            except Pyro5.errors.NamingError:
                sleep(timeout)
                timeout = increse_timeout(timeout)
    
    def workers_status(self):
        workers = self.workers()
        print('--------------------------------------------------')
        for worker in workers:
            w = direct_connect(worker[1])
            print(worker[0])
            status: dict = w.status
            for i in status.keys():
                print(f'  {i}: {status[i]}')
            print()
        print('--------------------------------------------------')

    def assign_groups(self) -> Dict:
        '''
        Get a dictionary of group:list[workers].
        '''
        timeout = self.timeout
        while True:
            try:
                workers = self.workers()
                if workers:
                    groups = {i:{'master': None, 'workers': []} for i in range(1, divide(len(workers), self._groups_len)+1)}

                    # Find workers without groups
                    workers_without_group = []
                    for worker in workers:
                        w = direct_connect(worker[1])
                        worker_master = w.master
                        worker_group = w.group
                        if not worker_group:
                            workers_without_group.append(worker)
                        else:
                            if not groups.get(worker_group):
                                workers_without_group.append(worker)
                            elif worker_master:
                                groups[worker_group]['master'] = worker
                                groups[worker_group]['workers'].append(worker)
                            else:
                                groups[worker_group]['workers'].append(worker)
                    
                    # Assign group to workers
                    for worker in workers_without_group:
                        sorted_groups = sorted([(group, len(groups[group]['workers'])) for group in groups], key=lambda x: x[1])
                        smaller = sorted_groups[0][0]
                        groups[smaller]['workers'].append(worker)
                    
                    # Move from group
                    while True:
                        if len(groups) >=2:
                            sorted_groups = sorted([(group, len(groups[group]['workers'])) for group in groups], key=lambda x: x[1])
                            first = sorted_groups[0]
                            last = sorted_groups[-1]
                            if first[1] < self._groups_len and last[1] > self._groups_len:
                                worker = random.choice(groups[last[0]]['workers'])
                                groups[last[0]]['workers'].remove(worker)
                                groups[first[0]]['workers'].append(worker)
                            else:
                                break
                        else:
                            break

                    # Assign master to groups
                    for group in groups:
                        if not groups[group]['master']:
                            groups[group]['master'] = random.choice([i for i in groups[group]['workers'] if i != groups[group]['master']])
                    
                    # Update nodes
                    if groups != self.groups:
                        for group in groups:
                            w = direct_connect(groups[group]['master'][1])
                            w.group = group
                            w.master = True
                            w.slaves = [i for i in groups[group]['workers'] if i != groups[group]['master']]
                            for i in groups[group]['workers']:
                                w = direct_connect(i[1])
                                if i != groups[group]['master']:
                                    w.slaves = []
                                    w.master = False
                                w_group =  w.group
                                if w_group:
                                    if w_group != group:
                                        w.group = group
                                        files = w.export_db(len(list(groups.keys())))
                                        for f, g in zip(files, groups.values()):
                                            master  = direct_connect(g['master'][1])
                                            master.import_db(f)
                                else:
                                    w.group = group
                        self.groups = groups
                        self.workers_status()
                sleep(self._timeout_groups)
            
            except Pyro5.errors.PyroError:
                sleep(timeout)
                timeout = increse_timeout(timeout)
    
    def group_masters(self):
        '''
        Get the list of masters.
        '''
        return [g['master'] for g in self.groups]

    def assign_workers(self, request: Tuple):
        '''
        Select workers that should do the next job.
        '''
        db_log.debug('excecute: assign_workers...')
        groups = self.groups
        if request[0] == ADD:
            g = random.choice(list(groups.keys()))
            return [groups[g]['master']]
        else:
            return [g['master'] for g in groups.values()]

    # TODO: TRY
    # FIX: random add
    def assign_jobs(self, workers: List[Tuple], request: Tuple, id: int):
        '''
        Send the request to the workers.
        '''
        db_log.debug('excecute: assign_jobs...')
        timeout = self.timeout
        for worker in workers:
            w = direct_connect(worker[1])
            while True:
                if not w.busy:
                    db_log.info(f'assing jobs: send work to {worker[0]}...\n')
                    w.run(request, id)
                    break
                else:
                    sleep(self.timeout)
                    timeout = increse_timeout(timeout)

    # TODO: TRY
    # TODO: What to do with the losed request results
    def get_results(self, workers: List[Tuple], id: int):
        '''
        Wait for the results.
        '''
        db_log.debug('excecute: get_results...')
        timeout = self.timeout
        self.results[id] = []
        for worker in workers:
            db_log.info(f'get results: wait responce from {worker[0]}...')
            try:
                w = direct_connect(worker[1])
                while True:
                    if not w.busy:
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
    
    # def print_groups(self, groups):
    #     g = {id:{w['master'][0]:[i[0] for i in w['workers']]} for id, w in groups}
    #     df = pd.DataFrame(g).transpose()
    #     print()
    #     print(g)
    #     print()
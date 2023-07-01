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



# FIX: What to do with existent db
# TODO: if dont get responce from server, repeat the requets to other server from the same group
# BUG: when you close the last node in one group

@Pyro5.api.expose
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
        self._groups: Dict[int, Dict[str, Tuple|List[Tuple]]] = {}
        self._group_workers = set()

        # LOCKS
        self.lock_id = Lock()
        self.lock_groups = Lock()
    
    def ping(self):
        return PING

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

    @property
    def groups_len(self):
        return self._groups_len
    
    @property
    def groups(self):
        with self.lock_groups:
            if not self._groups:
                workers = self.workers
                groups = {}
                for worker in workers:
                    try:
                        w = direct_connect(worker[1])
                        group = w.group
                        master = w.master
                        if group:
                            if groups.get(group):
                                groups[group]['master'] = master
                                groups[group]['workers'].append(worker)
                            else:
                                groups[group] = {'master':master, 'workers':[worker]}
                    except Pyro5.errors.PyroError:
                        pass
                self._groups = groups
            return self._groups

    @groups.setter
    def groups(self, groups: Dict):
        with self.lock_groups:
            self._groups = groups
    
    @property
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
    
    @property
    def masters(self):
        '''
        Get the list of masters.
        '''
        return [self.groups[g]['master'] for g in self.groups.keys()]
    
    # BUG: various groups with one worker
    # FIX: if loose lowers groups move currents
    def regroup(self, group: int, worker: Tuple):
        # If the worker alredy has a group assigned
        if group:
            # TODO: move workers from others groups if there is only one in this
            workers_alive = self.groups[group].copy()
            master = workers_alive['master']
            workers = workers_alive['workers'].copy()

            for check_worker in workers:
                if check_worker != worker:
                    try:
                        w = direct_connect(check_worker[1])
                        w.ping()
                    except Pyro5.errors.PyroError:
                        workers_alive['workers'].remove(check_worker)
            if worker != master:
                try:
                    m = direct_connect(master[1])
                    m.ping()
                except Pyro5.errors.PyroError:
                    workers_alive['master'] = worker
            
            # TODO: if len(group) > group_len
            # Move the worker in a group of only one to other group
            if len(workers_alive['workers'])  == 1:
                print('changing group\n')
                # sort by number of workers
                sorted_groups = sorted([(g, len(self.groups[g]['workers'])) for g in self.groups.keys() if group != g], key=lambda x: x[1])
                if len(sorted_groups):
                    self.groups.pop(group)
                    group = sorted_groups[0][0]
                    workers_alive = self.groups[group].copy()
                    workers_alive['workers'].append(worker)
            
            self.groups[group] = workers_alive
            if worker == workers_alive['master']:
                return group, workers_alive['master'], [x for x in workers_alive['workers'] if x != worker]
            else:
                return group, workers_alive['master'], []
        
        # Assign a group to worker
        # TODO: when add a node and the is a group with len(group) > group_len take both to new group
        # TODO: when and a node and it will be alone in a group... 
        else:
            groups = self.groups
            if groups:
                
                # Groups sorted by number of workers
                sorted_groups = sorted([(g, len(groups[g]['workers'])) for g in groups.keys()], key=lambda x: x[1])
                first_group = sorted_groups[0][0]
                last_group = sorted_groups[-1][0]
                
                new_group = 1
                for i, g in enumerate(sorted(list(groups.keys()))):
                    i+=1
                    if i != g:
                        new_group = i
                        break
                    else:
                        new_group = i+1

                # if there is a group with less workers than groups_len
                if len(groups[first_group]['workers']) < self.groups_len:
                    groups[first_group]['workers'].append(worker)
                    return first_group, groups[first_group]['master'], []
                
                # if there is a group with more workers than groups_len
                elif len(groups[last_group]['workers']) > self.groups_len:
                    take_worker = random.choice([_w for _w in groups[last_group]['workers'] if _w != groups[last_group]['master']])
                    # update the take_worker and his master
                    added = False
                    while not added:
                        try:
                            w = direct_connect(take_worker[1])
                            w.master = worker
                            w.slaves = []
                            w.group = new_group
                            added = True
                        except Pyro5.errors.PyroError:
                            sleep(self.timeout)
                    groups[new_group] = {'master':worker, 'workers':[worker, take_worker]}
                    return new_group, worker, [take_worker]
                
                else:
                    groups[new_group] = {'master':worker, 'workers':[worker]}
                    return new_group, worker, []
            # if not exist groups
            else:
                new_group = 1
                groups[new_group] = {'master':worker, 'workers':[worker]}
                return new_group, worker, []

    # FIX: TRY
    # BUG: what to do with desconected groups
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

    def workers_status(self):
        workers = self.workers
        print('--------------------------------------------------')
        for worker in workers:
            w = direct_connect(worker[1])
            print(worker[0])
            status: dict = w.status
            for i in status.keys():
                print(f'  {i}: {status[i]}')
            print()
        print('--------------------------------------------------')

    def locate_file(self, workers: List[Tuple], file_name: str):
        db_log.debug('execute: locate file...')
        for worker in workers:
            w = direct_connect(worker[1])
            # CHECK:
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
                while True:
                    if not w.busy:
                        db_log.info(
                            f'assing jobs: send work to {worker[0]}...\n')
                        w.run(request, id)
                        break
                    else:
                        sleep(self.timeout)
                        timeout = increse_timeout(timeout)

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


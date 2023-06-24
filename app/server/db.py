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


# TODO: when copy db also copy files
# TODO: move db in worker

# FIX: What to do with existent db
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
        self._groups: Dict[int, Dict[str, List | Tuple]] = {}
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
                    # FIX:
                    groups = {i: {'master': None, 'workers': []} for i in range(
                        1, divide(len(workers), self._groups_len)+1)}

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
                        sorted_groups = sorted(
                            [(group, len(groups[group]['workers'])) for group in groups], key=lambda x: x[1])
                        smaller = sorted_groups[0][0]
                        groups[smaller]['workers'].append(worker)

                    # Move from group
                    while True:
                        if len(groups) >= 2:
                            sorted_groups = sorted(
                                [(group, len(groups[group]['workers'])) for group in groups], key=lambda x: x[1])
                            first = sorted_groups[0]
                            last = sorted_groups[-1]
                            if first[1] < self._groups_len and last[1] > self._groups_len:
                                worker = random.choice(
                                    groups[last[0]]['workers'])
                                groups[last[0]]['workers'].remove(worker)
                                groups[first[0]]['workers'].append(worker)
                            else:
                                break
                        else:
                            break

                    # Assign master to groups
                    for group in groups:
                        if not groups[group]['master']:
                            groups[group]['master'] = random.choice(
                                [i for i in groups[group]['workers'] if i != groups[group]['master']])

                    # Update nodes
                    if groups != self.groups:
                        for group in groups:
                            w = direct_connect(groups[group]['master'][1])
                            w_group = w.group
                            if w_group:
                                if w_group != group:
                                    w.group = group
                                    files = w.export_db(
                                        len(list(groups.keys())))
                                    for f, g in zip(files, groups.values()):
                                        master = direct_connect(g['master'][1])
                                        master.import_db(f)
                            else:
                                w.group = group
                            w.master = True
                            w.slaves = [i for i in groups[group]
                                        ['workers'] if i != groups[group]['master']]

                            for i in groups[group]['workers']:
                                w = direct_connect(i[1])
                                if i != groups[group]['master']:
                                    w.slaves = []
                                    w.master = False
                                w_group = w.group
                                if w_group:
                                    if w_group != group:
                                        w.group = group
                                        w.clear_db()
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
        return [self.groups[g]['master'] for g in self.groups.keys()]

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
        workers = self.group_masters()
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

import random
from time import sleep
from typing import Tuple, List, Dict

from app.rpc.ns import *
from app.utils.thread import Kthread





# TODO: Create a model of distributed database
# TODO: When leader is created, resolve the db from workers

# TODO: divide by groups the workers to replicate the db
# NOTE: the replication must be resolved between groups
# TODO: When the number of grups decrease or grow is needed merge or split the groups db?

# TODO: Solo se puede hacer una tarea a la vez por nodo
# TODO: Create thread for bg replication

# TODO: Create clock

# TODO: what happend if a worker disconnect and then it reconnect to the network?

# FIX: If you do add with the same file it can be copied to differents db

# TODO: the request should be send to various nodes from the same group to do not lose it?

class DataBase:
    def __init__(self) -> None:
        self._job_id = 0

        # TODO: variate
        self._groups_number = 2
        self._timeout = 0.1
        
        # TODO: cache
        self.groups = {}

        self.results: Dict[int, List[dict]] = {}
        self.worker_prefix = 'worker-'
    
    # FIX: TRY
    def workers(self):
        '''
        Get the list of all availble workers.
        '''
        while True:
            try:
                ns = locate_ns()
                return list(ns.list(prefix=self.worker_prefix).items())
            except Pyro5.errors.NamingError:
                sleep(self._timeout)
    

    # TODO: what to do when the number of groups change?
    def assign_groups(self, workers: list, groups: Dict):
        '''
        Get the current grups and the workers without groups.
        Return the new groups with the workers added.
        '''
        smaller_groups = [(k, len(v)) for k, v in zip(groups.keys(), groups.values())]
        for i in range(self._groups_number):
            if i not in [x for x, y in smaller_groups]:
                smaller_groups.append((i, 0))
                groups[i] = []
        
        for i in workers:
            sorted_groups = sorted(smaller_groups, key=lambda x: x[1])
            smaller = sorted_groups[0][0]
            w = direct_connect(i[1])
            w.set_group(smaller)
            groups[smaller].append(i)
            x = smaller_groups.index(sorted_groups[0])
            x = smaller_groups.pop(x)
            x = (x[0], x[1]+1)
            smaller_groups.append(x)
        return groups


    # FIX: TRY
    # TODO: Use self.groups as cache
    def get_groups(self) -> Dict:
        '''
        Get a dictionary of group:list[workers].
        '''
        while True:
            try:
                workers = self.workers()
                groups = {}
                workers_without_group = []
                for worker in workers:
                    w = direct_connect(worker[1])
                    if w.group is None:
                        workers_without_group.append(worker)
                    else:
                        if groups.get(w.group) is None:
                            groups[w.group] = [worker]
                        else:
                            groups[w.group].append(worker)
                
                groups = self.assign_groups(workers_without_group, groups)
                return groups
            
            except Pyro5.errors.PyroError:
                sleep(self._timeout)
    

    def merge_results(self, results: List[dict]):
        '''
        Merge all the results given by the workers.
        '''
        if results and results[0] and list(results[0].keys())[0] == 'messagge':
            return {'messagge': 'correct'}
        else:
            r = {}
            for i in results:
                r.update(i)
            return r
    
    
    # FIX: TRY
    def execute(self, request: Tuple):
        job_id = self._job_id + 1
        self._job_id = job_id

        while True:
            try:
                workers = self.best_workers()
                self.assign_jobs(workers, request, job_id)
                self.get_results(workers, job_id)
                return self.merge_results(self.results[job_id])
            except Pyro5.errors.PyroError:
                sleep(self._timeout)

    # FIX: Method used to select what are the workers that should do the job
    def best_workers(self):
        '''
        Select workers that should do the next job.
        '''
        return [random.choice(x) for x in self.get_groups().values()]

    def assign_jobs(self, workers: List[Tuple], request: Tuple, id: int):
        '''
        Send the request to the workers.
        '''
        for worker in workers:
            print('send work to {}...'.format(worker))
            w = direct_connect(worker[1])
            w.run(request, id)

    def get_results(self, workers: List[Tuple], id: int):
        '''
        Wait for the results.
        '''
        self.results[id] = []
        for worker in workers:
            print('wait responce from {}...'.format(worker))
            w = direct_connect(worker[1])
            r = w.join(id)
            self.results[id].append(r)
    

    def replicate(self):
        ...
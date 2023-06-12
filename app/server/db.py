import random
from time import sleep
from typing import Tuple, List, Dict

from app.rpc.ns import *
from app.utils.utils import *
from app.utils.thread import Kthread



# TODO: commando add se manda solo a un grupo, los otros commandos se mandan a todos
# TODO: Se debe esperar a que todas las db del grupo esten en el mismo tiempo o mandar el request solo a la mas actualizada
# TODO: Thread para llevar las replicaciones de los grupos
# TODO: variable bussy para saber si se esta usando el recurso
# TODO: Llevar una cache de las request como cola de prioridad teniendo la request y el grupo que le corresponde, ejecutar en los no actualizados
# TODO: copiar la db mas actualizada a los nodos nuevos




# NOTE: the replication must be resolved between groups
# TODO: When the number of grups decrease or grow is needed merge or split the groups db?

# TODO: what happend if a worker disconnect and then it reconnect to the network?

# FIX: If you do add with the same file it can be copied to differents db


class DataBase:
    def __init__(self) -> None:
        self._job_id = 0
        self._requests = {}

        # TODO: variate
        self._groups_number = 2
        self._timeout = 0.1
        
        # TODO: cache
        self.groups = {}

        self.results: Dict[int, List[dict]] = {}
        self.worker_prefix = 'worker-'

        self._replicate = Kthread(
            target=self.replicate,
            daemon=True
        )
        self._replicate.start()
    
    # FIX: TRY
    def workers(self):
        '''
        Get the list of all availble workers.
        '''
        timeout = self._timeout
        while True:
            try:
                ns = locate_ns()
                return list(ns.list(prefix=self.worker_prefix).items())
            except Pyro5.errors.NamingError:
                sleep(timeout)
                timeout = increse_timeout(timeout)
    

    # TODO: what to do when the number of groups change?
    def assign_groups(self, workers: list, groups: Dict):
        '''
        Get the current grups and the workers without groups.
        Return the new groups with the workers added.
        '''
        # Get the groups name and his number of workers, and add empty group if not exist
        groups_len = []
        for i in range(1, self._groups_number+1):
            if i not in groups.keys():
                groups_len.append((i, 0))
                groups[i] = []
            else:
                groups_len.append((i, len(groups[i])))
        
        # Assign group to workers
        sorted_groups = groups_len
        for worker in workers:
            # Sort groups by number of workers
            sorted_groups = sorted(sorted_groups, key=lambda x: x[1])
            # get the smaller group
            smaller = sorted_groups[0][0]
            
            # connect to the current worker
            w = direct_connect(worker[1])
            # set the group
            w.set_group(smaller)
            # add the worker to the group list
            groups[smaller].append(worker)
            
            # then add it to the group_len list
            x = sorted_groups.pop(0)
            x = (x[0], x[1]+1)
            sorted_groups.append(x)
        return groups


    # FIX: TRY
    # TODO: Use self.groups as cache
    def get_groups(self) -> Dict:
        '''
        Get a dictionary of group:list[workers].
        '''
        timeout = self._timeout
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
                sleep(timeout)
                timeout = increse_timeout(timeout)
    

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
        self.add_request(request, job_id)

        timeout = self._timeout
        while True:
            try:
                # print('assign_workers...')
                workers = self.assign_workers(request)
                # print('add_request_workers...')
                self.add_request_workers(job_id, workers)
                # print('assign_jobs...')
                job_workers = self.get_workers_on_time(workers)
                self.assign_jobs(job_workers, request, job_id)
                # print('get_results...')
                self.get_results(job_workers, job_id)
                # print('assign_clocks...')
                # self.assign_clocks()
                # print('results...')
                return self.merge_results(self.results[job_id])
            except Pyro5.errors.PyroError:
                sleep(timeout)
                timeout = increse_timeout(timeout)

    def add_request(self, request: Tuple, id: int):
        self._requests[id] = {'request':request, 'workers': None}
    
    def add_request_workers(self, id: int, workers: List):
        if self._requests.get(id):
            self._requests[id]['workers'] = workers.copy()
        
    # def assign_clocks(self):
    #     for worker in self.workers():
    #         w = direct_connect(worker[1])
    #         if w.clock == self._job_id-1:
    #             w.set_clock(self._job_id)
    
    def assign_workers(self, request: Tuple):
        '''
        Select workers that should do the next job.
        '''
        groups = list(self.get_groups().values())
        if request[0] == 'add':
            return random.choice(groups)
        else:
            all = []
            for i in groups:
                all.extend(i)
            return all

    # TODO: TRY
    def assign_jobs(self, workers: List[Tuple], request: Tuple, id: int):
        '''
        Send the request to the workers.
        '''
        timeout = self._timeout
        
        for worker in workers:
            w = direct_connect(worker[1])
            while True:
                if not w.busy:
                    print('send work to {}...\n'.format(worker))
                    w.run(request, id)
                    break
                else:
                    sleep(self._timeout)
                    timeout = increse_timeout(timeout)
    
    def get_workers_on_time(self, workers: List):
        t = 0
        l = []
        print(f'workers: {[y for _, y in workers]}')
        for worker in workers:
            w = direct_connect(worker[1])
            print(worker[0], w.clock)
            wt = w.clock
            if wt > t:
                t = wt
                l = [worker]
            elif w.clock == t:
                l.append(worker)
        print(f'workers left: {[y for _, y in l]}\n')
        return l

    def get_results(self, workers: List[Tuple], id: int):
        '''
        Wait for the results.
        '''
        self.results[id] = []
        for worker in workers:
            print('wait responce from {}...'.format(worker))
            w = direct_connect(worker[1])
            r = w.join(id)
            print(f'results: {r}\n')
            self.results[id].append(r)
    
    # TODO: disconected nodes
    def replicate(self):
        while True:
            
            smaller_time = float('inf')
            worker_behind = None
            workers = self.workers()
            for worker in workers:
                try:
                    w = direct_connect(worker[1])
                    if w.clock < smaller_time:
                        smaller_time = w.clock
                        worker_behind = worker
                except Pyro5.errors.PyroError:
                    pass
            if worker_behind:
                try:
                    w = direct_connect(worker_behind[1])
                    if not w.busy:
                        ids = sorted(self._requests.keys())
                        for i in ids:
                            if w.clock > i:
                                self._requests.pop(i)
                            else:
                                if self._requests[i]['workers'] and worker in self._requests[i]['workers']:
                                    self.assign_jobs(worker_behind, self._requests[i]['request'], i)
                                else:
                                    w.set_clock(i)
                except Pyro5.errors.PyroError:
                    pass
            sleep(self._timeout)

                
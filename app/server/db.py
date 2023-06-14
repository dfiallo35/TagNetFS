import random
from time import sleep
from typing import Tuple, List, Dict

from app.rpc.ns import *
from app.utils.utils import *
from app.utils.thread import Kthread

db_log = log('data-base', logging.DEBUG)


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

# TODO: if dont get responce from server, repeat the requets to other server from the same group

# TODO: increse the clock of the workers that are right on time in add

# TODO: Master-slave distributed db

class DataBase:
    def __init__(self) -> None:
        self._job_id = 0
        self._requests = {}

        # TODO: variate
        self._groups_len = 2
        self._groups_number = 2
        self._timeout = 0.1
        
        # TODO: cache
        self.groups: Dict[int, Dict[str, List|Tuple]] = {}

        self.results: Dict[int, List[dict]] = {}
        self.worker_prefix = 'worker-'

        # self._replicate = Kthread(
        #     target=self.replicate,
        #     daemon=True
        # )
        # self._replicate.start()
    
    # OK
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


    
    
    # TODO:
    def group_masters(self):
        '''
        Get the list of masters.
        '''
        for group_workers in self.assign_groups():
            ...


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
                # job_workers = self.get_workers_on_time(workers)
                self.assign_jobs(workers, request, job_id)
                # print('get_results...')
                self.get_results(workers, job_id)
                # print('assign_clocks...')
                # self.assign_clocks()
                # print('results...')
                return self.merge_results(self.results[job_id])
            except Pyro5.errors.PyroError:
                sleep(timeout)
                timeout = increse_timeout(timeout)

    def add_request(self, request: Tuple, id: int):
        self._requests[id] = {'request':request, 'workers': []}
    
    def add_request_workers(self, id: int, workers: List):
        if self._requests.get(id):
            self._requests[id]['workers'] = workers.copy()
    
    # TODO: Use self.groups as cache
    # FIX: Can loose db in decrease the number or workers
    def assign_groups(self) -> Dict:
        '''
        Get a dictionary of group:list[workers].
        '''
        timeout = self._timeout
        while True:
            try:
                workers = self.workers()
                groups = {i:{'master': None, 'workers': []} for i in range(1, (len(workers)//self._groups_len)+1)}

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
                            w.set_group = None
                            workers_without_group.append(worker)
                        elif worker_master:
                            groups[worker_group]['master'] = worker
                            groups[worker_group]['workers'].append(worker)
                        else:
                            groups[worker_group]['workers'].append(worker)
                
                # Assign group to workers
                sorted_groups = [(group, len(groups[group]['workers'])) for group in groups]
                for worker in workers_without_group:
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

                # Assign master to groups
                for group in groups:
                    if not groups[group]['master']:
                        groups[group]['master'] = random.choice(groups[group]['workers'])
                return groups
            except Pyro5.errors.PyroError:
                sleep(timeout)
                timeout = increse_timeout(timeout)
    
    # DELETE
    def assign_workers(self, request: Tuple):
        '''
        Select workers that should do the next job.
        '''
        groups = list(self.assign_groups().values())
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
                    db_log.info(f'assing jobs: send work to {worker}...\n')
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

    # TODO: What to do with the losed request results
    def get_results(self, workers: List[Tuple], id: int):
        '''
        Wait for the results.
        '''
        timeout = self._timeout
        self.results[id] = []
        for worker in workers:
            db_log.info(f'get results: wait responce from {worker[0]}...')
            for _ in range(3):
                try:
                    w = direct_connect(worker[1])
                    while True:
                        if not w.busy:
                            r = w.get_result(id)
                            if r is not None:
                                db_log.info(f'results: {r}\n')
                                self.results[id].append(r)
                        sleep(self._timeout)
                        timeout = increse_timeout(timeout)
                except Pyro5.errors.PyroError:
                    pass
    
    # TODO: disconected nodes
    def replicate(self):
        while True:
            smaller_time = float('inf')
            workers_behind = []
            workers = self.workers()
            for worker in workers:
                try:
                    w = direct_connect(worker[1])
                    if w.clock < smaller_time:
                        smaller_time = w.clock
                        workers_behind = [worker]
                    elif w.clock == smaller_time:
                        workers_behind.append(worker)
                except Pyro5.errors.PyroError:
                    pass
            if workers_behind:
                db_log.info(f'replicate: workers_behind: {workers_behind}...')
                ids = sorted(self._requests.keys())
                for worker in workers_behind:
                    try:
                        w = direct_connect(worker[1])
                        if not w.busy and ids:
                            id = ids[0]
                            if w.clock >= id:
                                db_log.info(f'replicate: delete {id}')
                                self._requests.pop(id)
                            else:
                                if worker in self._requests[id]['workers']:
                                    db_log.info(f'replicate: assign job to {worker[0]}...')
                                    self.assign_jobs(worker, self._requests[id]['request'], id)
                                else:
                                    w.set_clock(id)
                    except Pyro5.errors.PyroError:
                        pass
            db_log.info('replicate: sleep...\n')
            sleep(2)

                
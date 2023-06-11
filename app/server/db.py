from typing import Tuple, List, Dict
from app.utils.thread import Kthread

from app.rpc.ns import *



# TODO: Create a model of distributed database
# TODO: When leader is created, resolve the db from workers

# TODO: divide by groups the workers to replicate the db

# TODO: Solo se puede hacer una tarea a la vez por nodo
# TODO: Create thread for bg replication

# TODO: Create clock

class DataBase:
    def __init__(self) -> None:
        self._job_id = 0
        self.jobs: Dict[int, List[Kthread]] = {}
        self.results: Dict[int, List[dict]] = {}

        self.worker_prefix = 'worker-'
    
    def workers(self):
        ns = locate_ns()
        return list(ns.list(prefix=self.worker_prefix).items())
    
    # FIX: Method used to select what are the workers that should do the job
    def best_workers(self):
        '''
        Select workers that should do the next job.
        '''
        workers = self.workers()
        return workers
    
    
    def merge_results(self, results: List[dict]):
        '''
        Merge all the results given by the workers
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

        ns = locate_ns()
        workers = self.best_workers()
        for worker in workers:
            print('send work to {}...'.format(worker))
            w = connect(ns, worker[0])
            w.run(request, job_id)
        
        # FIX: wait responce
        self.results[job_id] = []
        for worker in workers:
            print('wait responce from {}...'.format(worker))
            w = connect(ns, worker[0])
            r = w.join(job_id)
            self.results[job_id].append(r)

        print('return responce...')
        return self.merge_results(self.results[job_id])


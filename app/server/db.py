import random
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

# TODO: what happend if a worker disconnect and the it reconnect to the network?

# FIX: If you do add with the same file it can be copied to differents db

class DataBase:
    def __init__(self) -> None:
        self._job_id = 0

        self._groups_number = 2
        self.groups = {}

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
        return [random.choice(x) for x in self.get_groups().values()]
    
    # TODO: what to do when the nomber of groups change?
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
        
        ns = locate_ns()
        for i in workers:
            sorted_groups = sorted(smaller_groups, key=lambda x: x[1])
            smaller = sorted_groups[0][0]
            w = connect(ns, i[0])
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
        workers = self.workers()
        ns = locate_ns()
        groups = {}
        let_me_solo_her_workers = []
        for worker in workers:
            w = connect(ns, worker[0])
            if w.group is None:
                let_me_solo_her_workers.append(worker)
            else:
                if groups.get(w.group) is None:
                    groups[w.group] = [worker]
                else:
                    groups[w.group].append(worker)
        
        groups = self.assign_groups(let_me_solo_her_workers, groups)
        return groups
            

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


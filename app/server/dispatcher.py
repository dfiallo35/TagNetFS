import random
import Pyro5.api
from typing import Tuple, List

from app.utils.thread import Kthread
from app.utils.ns import *




@Pyro5.api.expose
class Dispatcher:
    def __init__(self):
        self.requests: dict[int:str] = {}
        self.current_id = 0
        self.get_id = 0

        self.worker_prefix = 'node-'

    # FIX: is adding the request and taking the next job
    def request(self, request: Tuple[str, List[str], List[str]] | Tuple[str, List[str]]):
        self.add(request)
        return self.dispatch_work()
        

    def add(self, request: Tuple[str, List[str], List[str]] | Tuple[str, List[str]]):
        self.requests[self.current_id] = request
        self.current_id += 1
    
    def get(self) -> Tuple[int, Tuple[str, List[str], List[str]]] | Tuple[int, Tuple[str, List[str]]]:
        if self.requests.get(self.get_id) is None:
            return  self.get_id, None
        
        petition = self.requests.pop(self.get_id)
        self.get_id += 1
        return self.get_id - 1, petition
    
    def workers(self):
        ns = locate_ns()
        return list(ns.list(prefix=self.worker_prefix).items())
    
    def dispatch_work(self):
        job = self.get()

        if job[1] is not None:
            workers = self.workers()
            worker_name = random.choice(workers)[0]
            ns = Pyro5.api.locate_ns()

            
            f = connect(ns, worker_name)
            return f.execute(job[1])
    



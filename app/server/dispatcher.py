import random
import Pyro5.api
from typing import Tuple, List

from app.rpc.ns import *
from app.server.db import DataBase




@Pyro5.api.expose
class Dispatcher:
    def __init__(self):
        self.db = DataBase()
        self.requests: dict[int:str] = {}
        self.current_id = 0
        self.get_id = 0

        self.worker_prefix = 'worker-'

    def ping(self):
        return 'OK'

    # FIX: make it async
    # FIX: TRY
    def request(self, request: Tuple):
        results = self.db.execute(request)
        return results
        
    # FIX: DELETE?
    def add(self, request: Tuple[str, List[str], List[str]] | Tuple[str, List[str]]):
        job_id = self.current_id + 1
        self.current_id = job_id
        self.requests[job_id] = request
        return job_id
    # FIX: DELETE?
    def get(self) -> Tuple[int, Tuple[str, List[str], List[str]]] | Tuple[int, Tuple[str, List[str]]]:
        if self.requests.get(self.get_id) is None:
            return  self.get_id, None
        petition = self.requests.pop(self.get_id)
        self.get_id += 1
        return self.get_id - 1, petition
    # FIX: DELETE?
    def workers(self):
        ns = locate_ns()
        return list(ns.list(prefix=self.worker_prefix).items())
    
    # TODO: Tomar un job y decidir el o los workers que lo deben ejecutar
    # TODO: Hacer db distribuida, dividoda en n grupos
    # TODO: replicacion y consistencia, se debe resolver en el propio grupo
    # NOTE: Cada server posee una db con los archivos que le pertenecen y con todos los tags de este
    # FIX: DELETE?
    def dispatch(self, request):
        if self.requests.get(self.get_id) is None:
            return  None
        request = self.requests.pop(id)
        results = self.db.execute(request)
        return results


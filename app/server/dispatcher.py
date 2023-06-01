import rpyc
from typing import Dict


@rpyc.service
class Dispatcher(rpyc.Service):
    def __init__(self):
        self.petitions: Dict[int:str] = {}
        self.current_id = 0
        self.get_id = 0
    
    @rpyc.exposed
    def add(self, petition: str):
        self.petitions[self.current_id] = petition
        self.current_id += 1
    
    @rpyc.exposed
    def get(self) -> str:
        if self.petitions.get(self.get_id) is None:
            return  self.get_id, None
        
        petition = self.petitions.pop(self.get_id)
        self.get_id += 1
        return self.get_id - 1, petition
        


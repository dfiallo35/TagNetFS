import Pyro5.api



@Pyro5.api.expose
class Dispatcher:
    def __init__(self):
        self.petitions: dict[int:str] = {}
        self.current_id = 0
        self.get_id = 0

    # TODO: should be async, and called by request
    def add(self, petition: str):
        self.petitions[self.current_id] = petition
        self.current_id += 1
    
    def get(self) -> str:
        if self.petitions.get(self.get_id) is None:
            return  self.get_id, None
        
        petition = self.petitions.pop(self.get_id)
        self.get_id += 1
        return self.get_id - 1, petition
        


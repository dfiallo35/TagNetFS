import Pyro5.api
import Pyro5.errors
from time import sleep
from typing import Tuple, List, Dict

from app.database.api import *
from app.utils.constant import *
from app.utils.utils import dirs_to_UploadFile
from app.utils.thread import Kthread
from app.utils.utils import *
from app.rpc.ns import *



@Pyro5.api.expose
class Worker():
    def __init__(self):
        self.database = DatabaseSession()
        self._requests = {}
        
        self._group = None
        self._master = False
        self._slaves = []
        self._replicate: Kthread = None
        
        self._job_id = 0
        self._busy = False
        
        self.results: Dict[int, dict] = {}
        self._timeout = 0.1

    def ping(self):
        return PING

    @property
    def clock(self):
        return self._job_id

    @property
    def master(self):
        return self._master

    @property
    def slaves(self):
        return self._slaves
    
    @property
    def group(self):
        return self._group
    
    @property
    def busy(self):
        return self._busy
    
    def set_group(self, group: int):
        self._group = group
    
    def set_clock(self, id: int):
        self._job_id = id
    
    # FIX
    def set_master(self, master: bool):
        if master:
            self._replicate = Kthread(
                target=self.replicate,
                daemon=True
            )
            self._replicate.start()
        else:
            if self._replicate:
                self._replicate.kill()
        self._master = master
    
    def set_slave(self, slave: Tuple):
        if slave not in self._slaves:
            self._slaves.append(slave)
    
    def get_result(self, id: int):
        if self.results.get(id) is not None:
            return self.results.pop(id)
        return None

    def get_db(self):
        return self.database.get_db()

    def run(self, request: Tuple, id: int):
        self._job_id = id
        self._requests[id] = request
        t = Kthread(
            target=self.execute,
            args=(request, id),
            daemon=True,
        )
        t.start()

    def execute(self, request: Tuple, id: int):
        self._busy = True
        match request[0]:
            case 'add':
                print('add executed...', end='\n')
                self.results[id] = add(dirs_to_UploadFile(request[1]), request[2], self.get_db())
            case 'delete':
                print('delete executed...', end='\n')
                self.results[id] =  delete(request[1], self.get_db())
            case 'list':
                print('list executed...', end='\n')
                self.results[id] =  qlist(request[1], self.get_db())
            case 'add-tags':
                print('add-tags executed...', end='\n')
                self.results[id] =  add_tags(request[1], request[2], self.get_db())
            case 'delete-tags':
                print('delete-tags executed...', end='\n')
                self.results[id] =  delete_tags(request[1], request[2], self.get_db())
            case _:
                print('Not job implemented')
        self._busy = False
    

    # TODO: disconected nodes
    # TODO: wait responce
    def replicate(self):
        while True:
            for slave in self.slaves:
                try:
                    w = direct_connect(slave[1])
                    w_clock = w.clock
                    if w_clock < self.clock:
                        if w_clock+1 in self._requests:
                            if not w.busy:
                                if self._requests[w_clock+1][0] == ADD:
                                    print(f'replicate: run add\n')
                                    w.run(self._requests[w_clock+1], w_clock+1)
                                else:
                                    print(f'replicate: set clock\n')
                                    w.set_clock(w_clock+1)
                        else:
                            # TODO
                            ...
                except Pyro5.errors.PyroError:
                    pass
            sleep(self._timeout)
        

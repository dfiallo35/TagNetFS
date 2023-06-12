import Pyro5.api
from time import sleep
from typing import Tuple, List, Dict

from app.database.api import *
from app.utils.utils import dirs_to_UploadFile
from app.utils.thread import Kthread
from app.utils.utils import *



@Pyro5.api.expose
class Worker():
    def __init__(self):
        self.database = DatabaseSession()
        self._group = None
        self._clock = 0
        self._job_id = 0
        self._busy = False
        
        self.results: Dict[int, dict] = {}
        self._timeout = 0.1

    def ping(self):
        return 'OK'
    
    @property
    def clock(self):
        return self._clock
    
    @property
    def group(self):
        return self._group
    
    @property
    def busy(self):
        return self._busy
    
    def set_group(self, group: int):
        self._group = group
    
    def set_clock(self, id: int):
        self._clock = id
    
    def get_result(self, id: int):
        if self.results.get(id) is not None:
            return self.results.pop(id)
        return None

    def join(self, id: int):
        timeout = self._timeout
        while True:
            if not self.busy:
                r = self.get_result(id)
                if r is not None:
                    return r
            sleep(self._timeout)
            timeout = increse_timeout(timeout)
    

    def get_db(self):
        return self.database.get_db()
    

    def run(self, request: Tuple, id: int):
        self._job_id = id
        print('set job ()...'.format(id), request)
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


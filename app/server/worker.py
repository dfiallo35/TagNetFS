import Pyro5.api
from typing import Tuple, List

from app.database.api import *



@Pyro5.api.expose
class Worker():
    def __init__(self):
        ...
    
    def execute(self, job: Tuple[str, List[str], List[str]] | Tuple[str, List[str]]):
        match job[0]:
            case 'add':
                print('add executed...', end='\n')
                
                return add(job[1], job[2])
            case 'delete':
                print('delete executed...', end='\n')
                return delete(job[1])
            case 'list':
                print('list executed...', end='\n')
                return qlist(job[1])
            case 'add-tags':
                print('add-tags executed...', end='\n')
                return add_tags(job[1], job[2])
            case 'delete-tags':
                print('delete-tags executed...', end='\n')
                return delete_tags(job[1], job[2])
            case _:
                print('Not job implemented')


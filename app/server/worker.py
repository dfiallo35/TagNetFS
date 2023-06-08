import Pyro5.api
from typing import Tuple, List

from app.database.api import *
from app.utils.utils import dirs_to_UploadFile



@Pyro5.api.expose
class Worker():
    def __init__(self):
        ...
    
    def execute(self, job: Tuple[str, List[str], List[str]] | Tuple[str, List[str]]):
        match job[0]:
            case 'add':
                print('add executed...', end='\n')
                return add(dirs_to_UploadFile(job[1]), job[2], get_db())
            case 'delete':
                print('delete executed...', end='\n')
                return delete(job[1], get_db())
            case 'list':
                print('list executed...', end='\n')
                return qlist(job[1], get_db())
            case 'add-tags':
                print('add-tags executed...', end='\n')
                return add_tags(job[1], job[2], get_db())
            case 'delete-tags':
                print('delete-tags executed...', end='\n')
                return delete_tags(job[1], job[2], get_db())
            case _:
                print('Not job implemented')


import Pyro5
import Pyro5.api
import Pyro5.errors
from typing import Tuple, List

from app.utils.utils import *
from app.rpc.ns import *


class Client:
    def run(request: Tuple[str, List[str], List[str]] | Tuple[str, List[str]]):
        try:
            ns = locate_ns()
            f = connect(ns, 'request')
            responce = f.request(request)
            print(responce)
            
        except Pyro5.errors.NamingError:
            print('NOT CONECTED...')


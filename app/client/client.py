from app.utils.utils import *

import Pyro5
import Pyro5.api
import Pyro5.errors
from Pyro5.api import Proxy
from Pyro5.nameserver import NameServer

from typing import Tuple, List



class Client:
    def run(request: Tuple[str, List[str], List[str]] | Tuple[str, List[str]]):
        try:
            ns: NameServer = Pyro5.api.locate_ns()
            uri = ns.lookup('request')
            f = Proxy(uri)
            f.add(request)
            print(f.get())
            
        except Pyro5.errors.NamingError:
            print('NOT CONECTED...')


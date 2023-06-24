import random
import Pyro5.api
from typing import Tuple, List

from app.rpc.ns import *
from app.server.db import DataBase




@Pyro5.api.expose
class Dispatcher:
    def __init__(self):
        self.db = DataBase()

    def ping(self):
        return PING

    # FIX: make it async?
    # FIX: TRY
    def request(self, request: Tuple):
        results = self.db.execute(request)
        return results

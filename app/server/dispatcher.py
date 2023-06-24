import random
import Pyro5.api
from typing import Tuple, List

from app.rpc.ns import *
from app.server.db import DataBase
from app.server.base_server import BaseServer

@Pyro5.api.expose
class Dispatcher(BaseServer):
    def __init__(self):
        self.db = DataBase()

    def ping(self):
        return PING

    # FIX: make it async?
    # FIX: TRY
    def request(self, request: Tuple):
        results = self.db.execute(request)
        return results

    def kill_threads(self):
        try:
            self.db.groups_thread.kill()
            if self.db.groups_thread.is_alive():
                self.db.groups_thread.join()
        except:
            pass
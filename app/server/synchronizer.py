import Pyro4, Pyro4.naming

import threading
import random
import time



@Pyro4.expose
class Synchronizer():
    def __init__(self) -> None:
        self.ns = Pyro4.naming.locateNS()
        self.interval = random.randint(10, 30)
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
    
    def run(self):
        print("Clock synchronizition interval: {} seconds".format(self.interval))
        while True:
            time.sleep(self.interval)
            
            ...

    def leader_election(self):
        ...
    
    def is_leader_active(self):
        ...
    
    def synchronize_clock(self):
        members = self.ns.list()



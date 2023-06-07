import threading
import random
import time



class Synchronizer():
    def __init__(self) -> None:
        self.ns = None
        self.interval = random.randint(10, 30)
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
    
    def run(self):
        print("Clock synchronizition interval: {} seconds".format(self.interval))
        while True:
            time.sleep(self.interval)
            
            ...
    
    def synchronize_clock(self):
        members = self.ns.list()



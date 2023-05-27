import Pyro4
from threading import Lock

counter = 0
counter_lock = Lock()


@Pyro4.expose
class LogicalClock:
    def __init__(self, initial_time=0):
        self.time = initial_time

    def get_time(self):
        return self.time

    def increment(self):
        with counter_lock:
            global counter
            counter += 1
            self.time = counter

    def adjust_time(self, other_time):
        with counter_lock:
            global counter
            counter = max(counter, other_time)
            self.time = counter


from app.utils.constant import *



class BaseServer:
    def kill_threads(self):
        raise NotImplementedError
    
    def ping(self):
        return PING
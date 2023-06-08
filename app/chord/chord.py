import socket
from time import sleep

from app.server.dispatcher import Dispatcher



# TODO: Comunication between nodes
class ChordNode:
    def __init__(self, id: int, nbits: int):
        self.id = id
        self.FT = [None] * nbits
        self.nodeSet = []
        
        self.nbits = nbits
        self.max = 2**nbits


    def run(self, others: list):
        '''
        Run the node.
        '''
        self.addNode(self.id)
        for i in others:
            self.addNode(i)
        self.recomputeFingerTable()

        while True:
            sleep(1)


    def addNode(self, id: int):
        self.nodeSet.append(int(id))
        self.nodeSet = list(set(self.nodeSet))
        self.nodeSet.sort()


    def delNode(self, id: int):
        assert id in self.nodeSet
        del self.nodeSet[self.nodeSet.index(id)]
        self.nodeSet.sort()


    def finger(self, i):
        '''
        Find the ith finger of the node.
        '''
        succ = (self.id + (2**(i-1))) % self.max
        start = self.nodeSet.index(self.id)
        end = (start + 1) % len(self.nodeSet)
        
        for k in range(len(self.nodeSet)):
            if self.between(succ, self.nodeSet[start] + 1, self.nodeSet[end] + 1):
                return self.nodeSet[end]
            start, end = end, ((end + 1) % len(self.nodeSet))
        return None


    def recomputeFingerTable(self):
        '''
        Recompute the finger table of the node.
        '''
        self.FT[0]  = self.nodeSet[self.nodeSet.index(self.id) - 1]
        self.FT[1:] = [self.finger(i) for i in range(1,self.nbits + 1)]


    def local_succ(self, key):
        '''
        Find the successor of the key in the node.
        '''
        if self.between(key, self.FT[0] + 1, self.id + 1):
            return self.id
        elif self.between(key, self.id + 1, self.FT[1]):
            return self.FT[1]
        for i in range(1, self.nbits + 1):
            if self.between(key, self.FT[i], self.FT[(i + 1) % self.nbits]):
                return self.FT[i]


    def between(self, key, start, end):
        '''
        Check if key is between start and end.
        ''' 
        if start < end:
            return start <= key < end
        else:
            return start <= key or key < end


    def print_info(self):
        print()
        print('Node: {}'.format(self.id))
        print('Predecessor: {}'.format(self.FT[0]))
        print('Successor: {}'.format(self.FT[1]))
        print('Finger Table: {}'.format(self.FT[1:-1]))
        print()


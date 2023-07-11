import networkx as nx
import networkx.algorithms.flow as flow
from tools import *

def get_digraph(M:list[list],n:int):
    bip_graph = nx.DiGraph()
    bip_graph.add_node((0, 0))
    bip_graph.add_node((3, 3))

    for i in range(n):
        bip_graph.add_node((i, 1))
        bip_graph.add_node((i, 2))
        bip_graph.add_edge((0, 0), (i, 1), capacity=1)
        bip_graph.add_edge((i, 2), (3, 3), capacity=1)

    for i in range(n):
        for j in range(n):
            if M[i][j]:
                bip_graph.add_edge((i, 1), (j, 2), capacity=1)

    return bip_graph


def solve(M:list[list]):
    n=len(M)
    bip_graph=get_digraph(M, n)
    max_flow=flow.maximum_flow_value(bip_graph, (0,0), (3,3))
    return max_flow


# n = 5
# M=[[0 for j in range(n)] for i in range(n)]

# M=paint(M, (4, 0, 4,4))
# M=paint(M, (1, 3, 3, 3))
# M=paint(M, (2, 1, 2,3))
# M=paint(M, (0, 0, 1,0))


# print_matrix(np.array(M))

# print(solve(M))
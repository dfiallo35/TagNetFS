from matrix_to_graph import *
import itertools


def graph_brute_force(M: list[list]):
    
    n = len(M)
    bg = Bipartite_Graph(M)
    
    if len(bg.edges) == 0:
        return 0
    
    for r in range(1, n + 1):
        
        combinations = list(itertools.combinations(list(bg.nodes), r))        
        for elem in combinations:
            bg_temp = bg.copy()

            for node in elem:
                bg_temp.remove_node(node[0], node[1])
            if len(bg_temp.edges) == 0:
                return r

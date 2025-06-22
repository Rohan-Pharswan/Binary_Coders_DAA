from heapq import heappush, heappop
import numpy as np

def heuristic(pos1, pos2):
    """Calculate Euclidean distance between two points."""
    return np.sqrt((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2)

def astar_path(graph, start, goal, positions):
    """
    Find the shortest path between start and goal using A* algorithm.
    Args:
        graph: NetworkX graph
        start: Starting node
        goal: Target node
        positions: Dictionary of node positions {node: (x, y)}
    Returns:
        path: List of nodes in the path
        cost: Total cost of the path
    """
    if start not in graph or goal not in graph:
        return None, float('inf')

    frontier = []
    heappush(frontier, (0, start))
    
    came_from = {start: None}
    cost_so_far = {start: 0}
    
    while frontier:
        current = heappop(frontier)[1]
        
        if current == goal:
            break
            
        for next_node in graph.neighbors(current):
            # Skip if the edge is blocked
            if graph[current][next_node].get('blocked', False):
                continue
                
            new_cost = cost_so_far[current] + graph[current][next_node]['weight']
            
            if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                cost_so_far[next_node] = new_cost
                priority = new_cost + heuristic(positions[next_node], positions[goal])
                heappush(frontier, (priority, next_node))
                came_from[next_node] = current
    
    if goal not in came_from:
        return None, float('inf')
    
    # Reconstruct path
    path = []
    current = goal
    total_cost = cost_so_far[goal]
    
    while current is not None:
        path.append(current)
        current = came_from[current]
    
    path.reverse()
    return path, total_cost 
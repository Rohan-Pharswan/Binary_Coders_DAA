from typing import Dict, List, Tuple, Set, Optional
import heapq
import networkx as nx
from collections import defaultdict

def compute_dijkstra(graph: nx.Graph, start: str, end: str) -> Tuple[List[str], float]:
    """
    Compute shortest path using Dijkstra's algorithm
    
    Args:
        graph: NetworkX graph object
        start: Starting node
        end: Ending node
        
    Returns:
        Tuple of (path list, total cost)
    """
    distances = {node: float('infinity') for node in graph.nodes()}
    distances[start] = 0
    previous = {node: None for node in graph.nodes()}
    pq = [(0, start)]
    visited = set()
    
    while pq:
        current_distance, current = heapq.heappop(pq)
        
        if current in visited:
            continue
            
        visited.add(current)
        
        if current == end:
            break
            
        for neighbor in graph.neighbors(current):
            if neighbor in visited:
                continue
                
            weight = graph.edges[current, neighbor]['weight']
            distance = current_distance + weight
            
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous[neighbor] = current
                heapq.heappush(pq, (distance, neighbor))
    
    if distances[end] == float('infinity'):
        return [], float('infinity')
        
    # Reconstruct path
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    
    return path, distances[end]

def find_alternative_routes(graph: nx.Graph, start: str, end: str, 
                          max_alternatives: int = 3, max_detour: float = 1.5) -> List[Tuple[List[str], float]]:
    """
    Find alternative routes between two points
    
    Args:
        graph: NetworkX graph object
        start: Starting location
        end: Ending location
        max_alternatives: Maximum number of alternative routes to find
        max_detour: Maximum allowed detour factor compared to shortest path
        
    Returns:
        List of tuples (path, cost) for each alternative route
    """
    # First find the shortest path and its cost
    shortest_path, min_cost = compute_dijkstra(graph, start, end)
    if not shortest_path:
        return []
        
    # Use k-shortest paths algorithm to find alternatives
    routes = []
    paths = nx.shortest_simple_paths(graph, start, end, weight='weight')
    
    for path in paths:
        if len(routes) >= max_alternatives:
            break
            
        cost = sum(graph.edges[path[i], path[i+1]]['weight'] for i in range(len(path)-1))
        if cost <= min_cost * max_detour:
            routes.append((path, cost))
    
    return routes

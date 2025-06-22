from typing import List, Dict, Tuple, Set
import numpy as np

def knapsack(items: List[Dict], capacity: float) -> Tuple[float, List[int]]:
    """
    Solve the 0/1 knapsack problem for supply allocation
    
    Args:
        items: List of dictionaries with 'name', 'value', and 'weight' keys
        capacity: Maximum weight capacity
        
    Returns:
        Tuple of (maximum value achievable, list of selected item indices)
    """
    n = len(items)
    # Create arrays for dynamic programming
    dp = np.zeros((n + 1, int(capacity) + 1), dtype=float)
    keep = np.zeros((n + 1, int(capacity) + 1), dtype=bool)
    
    # Fill the dynamic programming table
    for i in range(1, n + 1):
        for w in range(int(capacity) + 1):
            item_weight = int(items[i-1]['weight'])
            item_value = items[i-1]['value']
            
            if item_weight <= w:
                value_with_item = dp[i-1][w-item_weight] + item_value
                if value_with_item > dp[i-1][w]:
                    dp[i][w] = value_with_item
                    keep[i][w] = True
                else:
                    dp[i][w] = dp[i-1][w]
            else:
                dp[i][w] = dp[i-1][w]
    
    # Backtrack to find selected items
    selected = []
    w = int(capacity)
    for i in range(n, 0, -1):
        if keep[i][w]:
            selected.append(i-1)
            w -= int(items[i-1]['weight'])
    
    return dp[n][int(capacity)], selected

def multi_knapsack(items: List[Dict], vehicles: List[Dict]) -> List[Tuple[int, List[int]]]:
    """
    Solve multiple knapsack problems for multiple vehicles
    
    Args:
        items: List of dictionaries with 'name', 'value', and 'weight' keys
        vehicles: List of dictionaries with 'id' and 'capacity' keys
        
    Returns:
        List of tuples (vehicle_id, list of assigned item indices)
    """
    assignments = []
    remaining_items = items.copy()
    
    for vehicle in vehicles:
        if not remaining_items:
            break
            
        value, selected = knapsack(remaining_items, vehicle['capacity'])
        if selected:
            assignments.append((vehicle['id'], selected))
            # Remove selected items from remaining items
            remaining_items = [item for i, item in enumerate(remaining_items) 
                             if i not in selected]
    
    return assignments

def prioritize_supplies(demands: Dict[str, List[str]], supplies: List[Dict]) -> List[Dict]:
    """
    Prioritize supplies based on demand frequency
    
    Args:
        demands: Dictionary mapping locations to lists of needed supplies
        supplies: List of supply dictionaries
        
    Returns:
        List of supplies sorted by priority (most needed first)
    """
    # Count how many locations need each supply
    demand_counts = {}
    for location_demands in demands.values():
        for item in location_demands:
            demand_counts[item] = demand_counts.get(item, 0) + 1
    
    # Sort supplies by demand count (higher demand = higher priority)
    return sorted(supplies, 
                 key=lambda x: (demand_counts.get(x['name'], 0), x['value']/x['weight']),
                 reverse=True)

def optimize_load(items: List[Dict], capacity: float, priorities: Dict[str, int]) -> Tuple[float, List[int]]:
    """
    Optimize load considering both value and priority
    
    Args:
        items: List of dictionaries with 'name', 'value', and 'weight' keys
        capacity: Maximum weight capacity
        priorities: Dictionary mapping item names to priority values
        
    Returns:
        Tuple of (total value, list of selected item indices)
    """
    # Adjust item values based on priorities
    prioritized_items = []
    for item in items:
        priority_multiplier = priorities.get(item['name'], 1)
        prioritized_items.append({
            'name': item['name'],
            'value': item['value'] * priority_multiplier,
            'weight': item['weight']
        })
    
    return knapsack(prioritized_items, capacity)

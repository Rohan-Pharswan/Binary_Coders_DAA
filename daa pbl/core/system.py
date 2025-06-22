import matplotlib.pyplot as plt
import networkx as nx
from core.routing import compute_dijkstra
from core.astar import astar_path
from core.knapsack import knapsack
import numpy as np
import matplotlib.patches as patches
from matplotlib.widgets import Button
import os
from datetime import datetime

# Set matplotlib backend to non-interactive to prevent tkinter warnings
import matplotlib
matplotlib.use('Agg')

class DisasterReliefSystem:
    def __init__(self, supplies, vehicles, nodes, edges, demands):
        self.graph = nx.Graph()
        self.pos = {}
        self.supplies = supplies
        self.original_vehicles = vehicles.copy()  # Store original vehicles
        self.vehicles = vehicles.copy()
        self.routes_info = []
        self.supply_demand = demands or {}
        self.node_types = {}  # Store node types for visualization
        self.blocked_roads = set()  # Store blocked roads
        self.use_astar = True  # Use A* by default
        self.assignments = []  # Store assignments

        # Node color mapping
        self.type_colors = {
            "warehouse": "lightgreen",
            "affected": "#ff9999",
            "hospital": "#99ccff",
            "shelter": "#ffcc99",
            "affected area": "#ff9999"  # Add alias for affected area
        }

        for node in nodes:
            node_type = node["type"].lower()
            self.graph.add_node(node["name"], type=node_type)
            self.pos[node["name"]] = (node["x"], node["y"])
            self.node_types[node["name"]] = node_type

        for edge in edges:
            self.graph.add_edge(edge["from"], edge["to"], weight=edge["weight"], blocked=False)

    def block_road(self, from_node, to_node):
        """Block a road and recalculate routes."""
        if self.graph.has_edge(from_node, to_node):
            self.graph[from_node][to_node]['blocked'] = True
            self.blocked_roads.add(tuple(sorted([from_node, to_node])))
            self.recalculate_routes()
            return True
        return False

    def unblock_road(self, from_node, to_node):
        """Unblock a road and recalculate routes."""
        if self.graph.has_edge(from_node, to_node):
            self.graph[from_node][to_node]['blocked'] = False
            self.blocked_roads.discard(tuple(sorted([from_node, to_node])))
            self.recalculate_routes()
            return True
        return False

    def recalculate_routes(self):
        """Recalculate routes using existing assignments."""
        if not self.assignments:
            return

        self.routes_info = []  # Clear only routes
        warehouse = next(n for n, d in self.graph.nodes(data=True) if d['type'] == "warehouse")
        undelivered = []

        for assignment in self.assignments:
            location = assignment['location']
            vehicle = assignment['vehicle']
            items = assignment['items']

            try:
                path, cost = self.find_path(warehouse, location)
                if not path:
                    raise ValueError(f"No valid path found to {location}")

                print(f"🔄 Recalculating route to {location}")
                print(f"🚛 Vehicle {vehicle['id']} carrying: {items}")
                print(f"🛣️ New route: {path} | Cost: {cost}")

                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    label = f"V{vehicle['id']}: {', '.join(items)}"
                    self.routes_info.append(((u, v), label))

            except Exception as e:
                print(f"❌ Failed to find new route to {location}: {e}")
                undelivered.append(location)

        if undelivered:
            print(f"⚠️ Warning: Could not reroute to: {', '.join(undelivered)}")

    def run_simulation(self, save_img=False):
        """Run initial simulation and store assignments."""
        print("\n=== Running Simulation ===")
        self.assignments = []  # Clear previous assignments
        self.vehicles = self.original_vehicles.copy()
        self.routes_info = []
        
        warehouse = next(n for n, d in self.graph.nodes(data=True) if d['type'] == "warehouse")
        undelivered = []

        # Debug print
        print(f"Current supply demands: {self.supply_demand}")
        print(f"Available supplies: {self.supplies}")
        print(f"Available vehicles: {self.vehicles}")

        for location, needed_supplies in self.supply_demand.items():
            if not needed_supplies:  # Skip if no supplies needed
                continue

            if not self.vehicles:
                undelivered.append(location)
                continue

            vehicle = self.vehicles.pop(0)
            available = [item for item in self.supplies if item["name"] in needed_supplies]
            
            if not available:
                undelivered.append(location)
                continue

            try:
                print(f"\n📍 Planning delivery to {location}")
                print(f"Needed supplies: {needed_supplies}")
                print(f"Available supplies for delivery: {[item['name'] for item in available]}")

                value, selected_indexes = knapsack(available, vehicle["capacity"])
                selected_items = [available[i]["name"] for i in selected_indexes]

                print(f"Selected items for delivery: {selected_items}")
                
                path, cost = self.find_path(warehouse, location)
                if not path:
                    raise ValueError(f"No valid path found to {location}")
                    
                print(f"🔹 Route: {path} | Cost: {cost}")

                # Store assignment
                self.assignments.append({
                    'location': location,
                    'vehicle': vehicle,
                    'items': selected_items
                })

                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    label = f"V{vehicle['id']}: {', '.join(selected_items)}"
                    self.routes_info.append(((u, v), label))

            except Exception as e:
                print(f"❌ Could not compute path to {location}: {e}")
                undelivered.append(location)
                # Return vehicle to pool if delivery failed
                self.vehicles.append(vehicle)

        if undelivered:
            print(f"\n⚠️ Warning: Could not deliver to: {', '.join(undelivered)}")

        # Return the image filename from plot_annotated_graph
        return self.plot_annotated_graph(save=save_img)

    def find_path(self, start, end):
        """Find path using either A* or Dijkstra's algorithm."""
        if self.use_astar:
            return astar_path(self.graph, start, end, self.pos)
        return compute_dijkstra(self.graph, start, end)

    def plot_annotated_graph(self, save=False):
        plt.figure(figsize=(12, 8))
        ax = plt.gca()

        # Draw nodes with different colors based on type
        for node_type in set(self.node_types.values()):
            node_list = [node for node, type_ in self.node_types.items() if type_ == node_type]
            if node_list:
                nx.draw_networkx_nodes(
                    self.graph, self.pos,
                    nodelist=node_list,
                    node_color=self.type_colors.get(node_type, 'gray'),
                    node_size=1000,
                    label=node_type.capitalize()
                )

        nx.draw_networkx_labels(self.graph, self.pos, ax=ax, font_size=10)

        edge_labels = nx.get_edge_attributes(self.graph, 'weight')
        edge_count = {}

        for (u, v) in self.graph.edges():
            key = tuple(sorted((u, v)))
            edge_count[key] = edge_count.get(key, 0) + 1
            rad = 0.2 * edge_count[key]

            # Start with just the weight
            label = f"Weight: {edge_labels.get((u, v), edge_labels.get((v, u), ''))}"
            if self.graph[u][v].get('blocked', False):
                label = "BLOCKED\n" + label

            # If route info exists, add it too
            for route_edge, info in self.routes_info:
                if set((u, v)) == set(route_edge):
                    label += f"\n{info}"
                    break

            x0, y0 = self.pos[u]
            x1, y1 = self.pos[v]
            dx = x1 - x0
            dy = y1 - y0
            dist = np.hypot(dx, dy)
            norm = np.array([-dy, dx]) / dist
            control = ((x0 + x1) / 2 + rad * dist * norm[0],
                       (y0 + y1) / 2 + rad * dist * norm[1])

            # Draw blocked roads with red dashed lines
            is_blocked = self.graph[u][v].get('blocked', False)
            path = patches.Path(
                [self.pos[u], control, self.pos[v]],
                [patches.Path.MOVETO, patches.Path.CURVE3, patches.Path.CURVE3]
            )

            patch = patches.FancyArrowPatch(
                path=path,
                color='red' if is_blocked else 'gray',
                arrowstyle='-|>',
                linewidth=1.5,
                linestyle='--' if is_blocked else '-',
                mutation_scale=10
            )
            ax.add_patch(patch)

            def bezier_point(t):
                x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * control[0] + t ** 2 * x1
                y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * control[1] + t ** 2 * y1
                return x, y

            def bezier_angle(t):
                dx = 2 * (1 - t) * (control[0] - x0) + 2 * t * (x1 - control[0])
                dy = 2 * (1 - t) * (control[1] - y0) + 2 * t * (y1 - control[1])
                return np.degrees(np.arctan2(dy, dx))

            mid_x, mid_y = bezier_point(0.5)
            angle = bezier_angle(0.5)

            ax.text(
                mid_x, mid_y,
                label,
                fontsize=8,
                ha='center',
                va='center',
                rotation=angle,
                rotation_mode='anchor',
                color='red' if is_blocked else 'black',
                bbox=dict(
                    facecolor='white',
                    edgecolor='none',
                    pad=0.3,
                    alpha=0.85
                )
            )

        plt.legend(title="Location Types", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.title("🚨 Disaster Relief Network Routes", pad=20)
        plt.axis("off")
        plt.tight_layout()
        
        if save:
            print("Saving graph image...")  # Debug print
            # Use absolute path to ensure file is saved in the correct location
            static_dir = os.path.join(os.getcwd(), "static")
            os.makedirs(static_dir, exist_ok=True)
            
            # Generate timestamped filename directly
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"simulation_output_{timestamp}.png"
            image_path = os.path.join(static_dir, image_filename)
            
            plt.savefig(image_path, bbox_inches='tight', dpi=300)
            plt.close()  # Close the figure immediately to free memory
            print(f"Graph image saved successfully to: {image_path}")  # Debug print
            
            # Force flush to ensure file is written
            import sys
            sys.stdout.flush()
            
            # Return just the filename (not the full path) for Flask to use
            return image_filename
        else:
            plt.show()
            return None

    def add_new_node(self, name: str, node_type: str, x: float, y: float) -> dict:
        """
        Add a new node to the graph.
        
        Args:
            name: Name of the new node
            node_type: Type of node (warehouse, affected, hospital, shelter)
            x: X coordinate
            y: Y coordinate
            
        Returns:
            dict: {"success": bool, "image_filename": str or None}
        """
        try:
            if not name or not node_type:
                print("Error: Name and node type are required")
                return {"success": False, "image_filename": None}
            
            if name in self.graph:
                print(f"Error: Node {name} already exists")
                return {"success": False, "image_filename": None}
            
            node_type = node_type.lower()
            if node_type == "affected area":  # Handle alias
                node_type = "affected"
            
            if node_type not in self.type_colors:
                print(f"Error: Invalid node type '{node_type}'. Must be one of: {list(self.type_colors.keys())}")
                return {"success": False, "image_filename": None}
            
            self.graph.add_node(name, type=node_type)
            self.pos[name] = (x, y)
            self.node_types[name] = node_type
            
            # Initialize empty supply demand for non-warehouse nodes
            if node_type != "warehouse":
                self.supply_demand[name] = []
            
            # Recalculate routes and get image filename
            image_filename = self.run_simulation(save_img=True)
            print(f"Successfully added node {name} of type {node_type} at ({x}, {y})")
            return {"success": True, "image_filename": image_filename}
        
        except Exception as e:
            print(f"Error adding node: {str(e)}")
            return {"success": False, "image_filename": None}
        
    def delete_node(self, name: str) -> dict:
        """
        Delete a node from the graph.
        
        Args:
            name: Name of the node to delete
            
        Returns:
            dict: {"success": bool, "image_filename": str or None}
        """
        if name not in self.graph:
            return {"success": False, "image_filename": None}
            
        # Remove node from graph and all related data structures
        self.graph.remove_node(name)
        del self.pos[name]
        del self.node_types[name]
        
        if name in self.supply_demand:
            del self.supply_demand[name]
            
        # Remove any routes involving this node
        self.routes_info = [route for route in self.routes_info 
                          if name not in route[0]]
                          
        # Recalculate routes and get image filename
        image_filename = self.run_simulation(save_img=True)
        return {"success": True, "image_filename": image_filename}
        
    def update_node_supplies(self, name: str, new_supplies: list) -> dict:
        """
        Update supplies needed at a node.
        
        Args:
            name: Name of the node
            new_supplies: List of additional supplies needed
            
        Returns:
            dict: Status of the update including success and any warnings
        """
        if name not in self.graph:
            print(f"Node {name} not found in graph")
            return {"success": False, "error": "Node not found"}
            
        node_type = self.node_types[name]
        if node_type == "warehouse":
            print(f"Cannot update supplies for warehouse")
            return {"success": False, "error": "Cannot update warehouse supplies"}
            
        print(f"Current supplies for {name}: {self.supply_demand[name]}")
        print(f"Adding new supplies: {new_supplies}")
        
        # Food and non-food item lists for validation
        food_items = [
            'water', 'food', 'rice', 'bread', 'milk', 'juice', 'soup', 'cereal', 
            'pasta', 'beans', 'vegetables', 'fruits', 'meat', 'fish', 'eggs', 
            'cheese', 'yogurt', 'butter', 'oil', 'sugar', 'salt', 'flour', 
            'canned food', 'dried food', 'baby food', 'formula', 'snacks', 
            'chocolate', 'cookies', 'crackers', 'nuts', 'seeds', 'honey', 
            'jam', 'sauce', 'condiments', 'beverages', 'tea', 'coffee',
            'pizza', 'burger', 'sandwich', 'hot dog', 'taco', 'burrito',
            'sushi', 'salad', 'soup', 'stew', 'curry', 'noodles', 'spaghetti',
            'lasagna', 'macaroni', 'potato', 'tomato', 'onion', 'garlic',
            'carrot', 'broccoli', 'spinach', 'lettuce', 'cabbage', 'cauliflower',
            'pepper', 'cucumber', 'mushroom', 'corn', 'peas', 'beans',
            'apple', 'banana', 'orange', 'grape', 'strawberry', 'blueberry',
            'raspberry', 'blackberry', 'peach', 'pear', 'plum', 'cherry',
            'lemon', 'lime', 'grapefruit', 'pineapple', 'mango', 'papaya',
            'avocado', 'coconut', 'olive', 'raisin', 'prune', 'date',
            'beef', 'pork', 'chicken', 'turkey', 'lamb', 'duck', 'goose',
            'bacon', 'sausage', 'ham', 'pepperoni', 'salami', 'prosciutto',
            'salmon', 'tuna', 'cod', 'shrimp', 'crab', 'lobster', 'clam',
            'oyster', 'mussel', 'squid', 'octopus', 'anchovy', 'sardine',
            'cake', 'pie', 'donut', 'muffin', 'croissant', 'bagel', 'biscuit',
            'pancake', 'waffle', 'french toast', 'omelette', 'scrambled eggs',
            'fried eggs', 'boiled eggs', 'poached eggs', 'deviled eggs',
            'ice cream', 'yogurt', 'pudding', 'custard', 'jello', 'gelatin',
            'candy', 'gum', 'lollipop', 'caramel', 'toffee', 'fudge',
            'popcorn', 'chips', 'pretzel', 'cheese puff', 'corn chip',
            'salsa', 'guacamole', 'hummus', 'dip', 'spread', 'butter',
            'margarine', 'mayonnaise', 'mustard', 'ketchup', 'relish',
            'pickle', 'olive', 'caper', 'herb', 'spice', 'seasoning',
            'vinegar', 'lemon juice', 'lime juice', 'orange juice',
            'apple juice', 'grape juice', 'cranberry juice', 'tomato juice',
            'vegetable juice', 'smoothie', 'milkshake', 'hot chocolate',
            'cocoa', 'coffee', 'tea', 'herbal tea', 'green tea', 'black tea',
            'white tea', 'oolong tea', 'chai tea', 'mint tea', 'chamomile tea',
            'food', 'meal', 'nutrition', 'protein', 'vitamin', 'mineral',
            'carbohydrate', 'fat', 'fiber', 'calorie', 'nutrient', 'diet',
            'breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'appetizer',
            'main course', 'side dish', 'beverage', 'drink', 'refreshment'
        ]
        
        non_food_items = [
            'medicine', 'blankets', 'clothing', 'tents', 'tools', 'batteries', 
            'flashlights', 'generators', 'fuel', 'hygiene', 'soap', 'toothpaste', 
            'shampoo', 'toilet paper', 'diapers', 'bandages', 'first aid', 
            'medical supplies', 'equipment', 'machinery', 'electronics', 
            'communication', 'radios', 'phones', 'computers', 'books', 
            'educational materials', 'toys', 'games', 'sports equipment', 
            'construction materials', 'building supplies', 'furniture', 
            'bedding', 'pillows', 'mattresses', 'cooking utensils', 'pots', 
            'pans', 'plates', 'cups', 'cutlery', 'storage containers', 
            'bags', 'backpacks', 'shoes', 'boots', 'hats', 'gloves', 
            'protective gear', 'masks', 'goggles', 'helmets', 'vests',
            'blanket', 'towel', 'sheet', 'curtain', 'carpet', 'rug',
            'medicine', 'pill', 'tablet', 'capsule', 'syrup', 'ointment',
            'cream', 'lotion', 'gel', 'spray', 'inhaler', 'injection',
            'bandage', 'gauze', 'tape', 'splint', 'cast', 'brace',
            'wheelchair', 'crutch', 'walker', 'cane', 'stretcher',
            'thermometer', 'stethoscope', 'blood pressure', 'monitor',
            'defibrillator', 'oxygen', 'ventilator', 'dialysis',
            'surgical', 'scalpel', 'forceps', 'clamp', 'suture',
            'disinfectant', 'antiseptic', 'sanitizer', 'alcohol',
            'glove', 'mask', 'gown', 'cap', 'shoe cover', 'apron',
            'equipment', 'device', 'apparatus', 'instrument', 'tool',
            'machine', 'motor', 'engine', 'pump', 'compressor', 'fan',
            'heater', 'cooler', 'refrigerator', 'freezer', 'oven',
            'stove', 'microwave', 'blender', 'mixer', 'grinder',
            'drill', 'saw', 'hammer', 'screwdriver', 'wrench', 'pliers',
            'wire', 'cable', 'pipe', 'tube', 'valve', 'connector',
            'battery', 'charger', 'adapter', 'converter', 'transformer',
            'generator', 'solar panel', 'wind turbine', 'fuel cell',
            'gasoline', 'diesel', 'propane', 'natural gas', 'kerosene',
            'lamp', 'bulb', 'light', 'lantern', 'candle', 'torch',
            'radio', 'television', 'speaker', 'microphone', 'antenna',
            'phone', 'mobile', 'smartphone', 'tablet', 'laptop',
            'computer', 'printer', 'scanner', 'camera', 'projector',
            'book', 'magazine', 'newspaper', 'journal', 'manual',
            'document', 'form', 'chart', 'map', 'calendar', 'clock',
            'watch', 'timer', 'stopwatch', 'alarm', 'bell', 'whistle',
            'toy', 'game', 'puzzle', 'card', 'dice', 'board',
            'ball', 'bat', 'racket', 'net', 'goal', 'target',
            'rope', 'chain', 'cable', 'wire', 'string', 'thread',
            'fabric', 'cloth', 'textile', 'fiber', 'yarn', 'wool',
            'cotton', 'silk', 'linen', 'nylon', 'polyester', 'leather',
            'plastic', 'rubber', 'metal', 'wood', 'glass', 'ceramic',
            'paper', 'cardboard', 'foam', 'sponge', 'brush', 'broom',
            'mop', 'bucket', 'container', 'box', 'bag', 'basket',
            'shelf', 'rack', 'stand', 'table', 'chair', 'bench',
            'bed', 'mattress', 'pillow', 'cushion', 'carpet', 'rug',
            'curtain', 'blind', 'shade', 'screen', 'partition', 'wall',
            'door', 'window', 'gate', 'fence', 'barrier', 'sign',
            'label', 'tag', 'sticker', 'tape', 'glue', 'adhesive',
            'nail', 'screw', 'bolt', 'nut', 'washer', 'rivet',
            'hinge', 'lock', 'key', 'handle', 'knob', 'button',
            'switch', 'lever', 'pedal', 'wheel', 'gear', 'pulley',
            'spring', 'shock', 'damper', 'filter', 'screen', 'mesh',
            'net', 'fence', 'barrier', 'wall', 'partition', 'divider'
        ]
        
        # Add new supplies to the system's available supplies if they don't exist
        for supply in new_supplies:
            if not any(s["name"] == supply for s in self.supplies):
                print(f"Adding new supply type to system: {supply}")
                
                # Determine if it's a food item for weight calculation
                supply_lower = supply.lower()
                is_food = any(item in supply_lower for item in food_items)
                is_non_food = any(item in supply_lower for item in non_food_items)
                
                # Default values
                base_weight = 2.0
                base_value = 10.0
                
                # Apply food weight increase (10% more for food items)
                if is_food and not is_non_food:
                    final_weight = base_weight * 1.1  # 10% increase for food
                    print(f"Food item detected: {supply}, weight adjusted to {final_weight}")
                else:
                    final_weight = base_weight
                
                # Add new supply with calculated values
                self.supplies.append({
                    "name": supply,
                    "value": base_value,
                    "weight": final_weight
                })
        
        # Add new supplies to node's demand
        if name not in self.supply_demand:
            self.supply_demand[name] = []
        
        self.supply_demand[name].extend(new_supplies)
        # Remove duplicates while preserving order
        self.supply_demand[name] = list(dict.fromkeys(self.supply_demand[name]))
        
        print(f"Updated supplies for {name}: {self.supply_demand[name]}")
        print(f"Total available supplies in system: {[s['name'] for s in self.supplies]}")
        
        # Check if we have enough vehicles for all demands
        total_locations = len([n for n in self.graph.nodes if self.node_types[n] != "warehouse" and n in self.supply_demand])
        available_vehicles = len(self.original_vehicles)
        
        # Reset assignments and vehicles for recalculation
        self.assignments = []
        self.vehicles = self.original_vehicles.copy()
        self.routes_info = []
        
        print("Running simulation with updated supplies...")
        # Recalculate routes with new supplies
        image_filename = self.run_simulation(save_img=True)
        print("Simulation completed")
        
        # Check if we had any undelivered locations
        if total_locations > available_vehicles:
            return {
                "success": True,
                "warning": "Not enough vehicles to deliver to all locations. Consider adding more vehicles.",
                "vehicles_needed": total_locations - available_vehicles,
                "image_filename": image_filename
            }
            
        return {"success": True, "image_filename": image_filename}

    def connect_new_node(self, from_node: str, to_node: str, weight: float) -> dict:
        """
        Add an edge between nodes.
        
        Args:
            from_node: Starting node
            to_node: Ending node
            weight: Edge weight
            
        Returns:
            dict: {"success": bool, "image_filename": str or None}
        """
        print(f"Attempting to connect {from_node} to {to_node} with weight {weight}")
        
        if from_node not in self.graph:
            print(f"Error: Node {from_node} not found in graph")
            return {"success": False, "image_filename": None}
            
        if to_node not in self.graph:
            print(f"Error: Node {to_node} not found in graph")
            return {"success": False, "image_filename": None}
            
        try:
            self.graph.add_edge(from_node, to_node, weight=weight, blocked=False)
            print(f"Successfully added edge between {from_node} and {to_node}")
            
            # Recalculate routes and get image filename
            image_filename = self.run_simulation(save_img=True)
            return {"success": True, "image_filename": image_filename}
        except Exception as e:
            print(f"Error adding edge: {str(e)}")
            return {"success": False, "image_filename": None}

    def add_warehouse_supplies(self, warehouse_name: str, new_supplies: list) -> dict:
        """
        Add new supplies to a warehouse with weight and value specifications.
        
        Args:
            warehouse_name: Name of the warehouse
            new_supplies: List of dictionaries with supply details
                         [{"name": "supply_name", "weight": weight, "value": value, "category": "food/non-food", "food_type": "solid/liquid"}]
            
        Returns:
            dict: Status of the update including success and any warnings
        """
        if warehouse_name not in self.graph:
            print(f"Warehouse {warehouse_name} not found in graph")
            return {"success": False, "error": "Warehouse not found"}
            
        node_type = self.node_types[warehouse_name]
        if node_type != "warehouse":
            print(f"Node {warehouse_name} is not a warehouse")
            return {"success": False, "error": "Node is not a warehouse"}
            
        print(f"Adding new supplies to warehouse {warehouse_name}: {new_supplies}")
        
        # Add new supplies to the system's available supplies
        for supply_data in new_supplies:
            supply_name = supply_data.get("name")
            weight = supply_data.get("weight", 2.0)
            value = supply_data.get("value", 10.0)
            category = supply_data.get("category", "non-food")
            food_type = supply_data.get("food_type", None)
            
            if not supply_name:
                continue
                
            # Check if supply already exists
            existing_supply = next((s for s in self.supplies if s["name"] == supply_name), None)
            
            if existing_supply:
                # Update existing supply with new values
                existing_supply["weight"] = weight
                existing_supply["value"] = value
                existing_supply["category"] = category
                existing_supply["food_type"] = food_type
                print(f"Updated existing supply: {supply_name}")
            else:
                # Add new supply
                new_supply = {
                    "name": supply_name,
                    "weight": weight,
                    "value": value,
                    "category": category,
                    "food_type": food_type
                }
                self.supplies.append(new_supply)
                print(f"Added new supply to system: {supply_name}")
        
        print(f"Total available supplies in system: {[s['name'] for s in self.supplies]}")
        
        # Recalculate routes and get image filename
        image_filename = self.run_simulation(save_img=True)
        print("Simulation completed with new warehouse supplies")
        
        return {
            "success": True, 
            "message": f"Successfully added supplies to warehouse {warehouse_name}",
            "image_filename": image_filename
        }

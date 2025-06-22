from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from core.system import DisasterReliefSystem
from datetime import datetime
import os
import json
import pickle
import uuid
import matplotlib.pyplot as plt
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'
app.config['LOGS_FOLDER'] = 'logs'

# Create logs directory if it doesn't exist
os.makedirs(app.config['LOGS_FOLDER'], exist_ok=True)

# Store the current system instance
current_system = None

# Small demo scenario data
SMALL_DEMO = {
    "supplies": [
        {"name": "Water", "value": 10, "weight": 3.3, "category": "food", "food_type": "liquid"},
        {"name": "Food", "value": 8, "weight": 2.2, "category": "food", "food_type": "solid"},
        {"name": "Medicine", "value": 15, "weight": 1, "category": "non-food", "food_type": None},
        {"name": "Blankets", "value": 5, "weight": 4, "category": "non-food", "food_type": None}
    ],
    "vehicles": [
        {"id": 1, "name": "Truck 1", "capacity": 20, "status": "available"},
        {"id": 2, "name": "Van 1", "capacity": 10, "status": "available"},
        {"id": 3, "name": "Emergency Vehicle", "capacity": 15, "status": "available"}
    ],
    "nodes": [
        {"name": "Central Warehouse", "type": "Warehouse", "x": 50, "y": 50},
        {"name": "Hospital A", "type": "Hospital", "x": 20, "y": 80},
        {"name": "Shelter B", "type": "Shelter", "x": 80, "y": 20},
        {"name": "Affected Area C", "type": "Affected", "x": 70, "y": 70},
        {"name": "Medical Center", "type": "Hospital", "x": 30, "y": 30},
        {"name": "Community Shelter", "type": "Shelter", "x": 90, "y": 50}
    ],
    "edges": [
        {"from": "Central Warehouse", "to": "Hospital A", "weight": 5},
        {"from": "Central Warehouse", "to": "Shelter B", "weight": 4},
        {"from": "Central Warehouse", "to": "Medical Center", "weight": 3},
        {"from": "Hospital A", "to": "Affected Area C", "weight": 2},
        {"from": "Shelter B", "to": "Affected Area C", "weight": 3},
        {"from": "Medical Center", "to": "Community Shelter", "weight": 4},
        {"from": "Affected Area C", "to": "Community Shelter", "weight": 3},
        {"from": "Hospital A", "to": "Medical Center", "weight": 6}
    ],
    "demands": {
        "Hospital A": ["Medicine", "Water"],
        "Shelter B": ["Food", "Water", "Blankets"],
        "Affected Area C": ["Water", "Food", "Medicine", "Blankets"],
        "Medical Center": [],  # Removed initial demands
        "Community Shelter": ["Food", "Blankets", "Water"]
    }
}

# Large demo scenario data
LARGE_DEMO = {
    "supplies": [
        {"name": "Water", "value": 10, "weight": 3.3, "category": "food", "food_type": "liquid"},
        {"name": "Food", "value": 8, "weight": 2.2, "category": "food", "food_type": "solid"},
        {"name": "Medicine", "value": 15, "weight": 1, "category": "non-food", "food_type": None},
        {"name": "Blankets", "value": 5, "weight": 4, "category": "non-food", "food_type": None},
        {"name": "First Aid", "value": 12, "weight": 2, "category": "non-food", "food_type": None},
        {"name": "Emergency Kit", "value": 20, "weight": 5, "category": "non-food", "food_type": None}
    ],
    "vehicles": [
        {"id": 1, "name": "Large Truck", "capacity": 30, "status": "available"},
        {"id": 2, "name": "Medical Van", "capacity": 15, "status": "available"},
        {"id": 3, "name": "Emergency Vehicle 1", "capacity": 20, "status": "available"},
        {"id": 4, "name": "Supply Truck", "capacity": 25, "status": "available"},
        {"id": 5, "name": "Rapid Response", "capacity": 10, "status": "available"}
    ],
    "nodes": [
        {"name": "Main Warehouse", "type": "Warehouse", "x": 50, "y": 50},
        {"name": "Secondary Warehouse", "type": "Warehouse", "x": 80, "y": 80},
        {"name": "City Hospital", "type": "Hospital", "x": 30, "y": 70},
        {"name": "Rural Hospital", "type": "Hospital", "x": 70, "y": 30},
        {"name": "Emergency Center", "type": "Hospital", "x": 20, "y": 20},
        {"name": "North Shelter", "type": "Shelter", "x": 40, "y": 90},
        {"name": "South Shelter", "type": "Shelter", "x": 90, "y": 40},
        {"name": "East Shelter", "type": "Shelter", "x": 85, "y": 15},
        {"name": "West Shelter", "type": "Shelter", "x": 15, "y": 85},
        {"name": "Downtown Area", "type": "Affected", "x": 60, "y": 60},
        {"name": "Coastal Region", "type": "Affected", "x": 25, "y": 45},
        {"name": "Mountain Area", "type": "Affected", "x": 75, "y": 65}
    ],
    "edges": [
        {"from": "Main Warehouse", "to": "City Hospital", "weight": 4},
        {"from": "Main Warehouse", "to": "North Shelter", "weight": 3},
        {"from": "Main Warehouse", "to": "Downtown Area", "weight": 2},
        {"from": "Secondary Warehouse", "to": "Rural Hospital", "weight": 4},
        {"from": "Secondary Warehouse", "to": "South Shelter", "weight": 3},
        {"from": "Secondary Warehouse", "to": "Mountain Area", "weight": 5},
        {"from": "City Hospital", "to": "West Shelter", "weight": 2},
        {"from": "City Hospital", "to": "Coastal Region", "weight": 3},
        {"from": "Rural Hospital", "to": "East Shelter", "weight": 4},
        {"from": "Rural Hospital", "to": "Mountain Area", "weight": 3},
        {"from": "Emergency Center", "to": "Coastal Region", "weight": 4},
        {"from": "Emergency Center", "to": "West Shelter", "weight": 5},
        {"from": "North Shelter", "to": "Downtown Area", "weight": 3},
        {"from": "South Shelter", "to": "Mountain Area", "weight": 2},
        {"from": "East Shelter", "to": "Rural Hospital", "weight": 4},
        {"from": "West Shelter", "to": "Coastal Region", "weight": 3},
        {"from": "Downtown Area", "to": "Mountain Area", "weight": 4},
        {"from": "Coastal Region", "to": "City Hospital", "weight": 3}
    ],
    "demands": {
        "City Hospital": ["Medicine", "First Aid", "Water", "Emergency Kit"],
        "Rural Hospital": ["Medicine", "Water", "First Aid"],
        "Emergency Center": ["Medicine", "First Aid", "Emergency Kit"],
        "North Shelter": ["Food", "Water", "Blankets"],
        "South Shelter": ["Food", "Water", "Blankets", "First Aid"],
        "East Shelter": ["Food", "Blankets", "Water"],
        "West Shelter": ["Food", "Water", "Emergency Kit"],
        "Downtown Area": ["Water", "Food", "Medicine", "Emergency Kit"],
        "Coastal Region": ["Water", "Food", "First Aid", "Blankets"],
        "Mountain Area": ["Food", "Blankets", "Emergency Kit", "Medicine"]
    }
}

def validate_positive_number(value, field_name):
    try:
        num = float(value)
        if num <= 0:
            raise ValueError(f"{field_name} must be greater than 0")
        return num
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field_name}")

@app.route("/", methods=["GET"])
def welcome():
    return render_template("welcome.html")

@app.route("/landing", methods=["GET"])
def landing():
    return render_template("landing.html")

@app.route("/index", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/block_road", methods=["POST"])
def block_road():
    global current_system
    try:
        data = request.get_json()
        from_node = data.get('from')
        to_node = data.get('to')
        
        if not from_node or not to_node:
            return jsonify({"error": "Both start and end nodes are required"}), 400
            
        if not current_system:
            return jsonify({"error": "No active simulation"}), 400
            
        if current_system.block_road(from_node, to_node):
            # Rerun simulation with blocked road and get the actual filename
            image_filename = current_system.run_simulation(save_img=True)
            
            return jsonify({
                "success": True,
                "message": f"Road from {from_node} to {to_node} blocked",
                "image": image_filename
            })
        else:
            return jsonify({"error": "Road not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/unblock_road", methods=["POST"])
def unblock_road():
    global current_system
    try:
        data = request.get_json()
        from_node = data.get('from')
        to_node = data.get('to')
        
        if not from_node or not to_node:
            return jsonify({"error": "Both start and end nodes are required"}), 400
            
        if not current_system:
            return jsonify({"error": "No active simulation"}), 400
            
        if current_system.unblock_road(from_node, to_node):
            # Rerun simulation with unblocked road and get the actual filename
            image_filename = current_system.run_simulation(save_img=True)
            
            return jsonify({
                "success": True,
                "message": f"Road from {from_node} to {to_node} unblocked",
                "image": image_filename
            })
        else:
            return jsonify({"error": "Road not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/run", methods=["POST"])
def run_simulation():
    global current_system
    try:
        # Extract and validate supplies
        supplies = []
        supply_count = int(request.form.get("supply_count", 0))
        
        if supply_count == 0:
            return jsonify({"error": "Please add at least one supply item."}), 400
            
        for i in range(supply_count):
            name = request.form.get(f"supply_name_{i}")
            if not name:
                return jsonify({"error": f"Supply name is required for item {i+1}"}), 400
                
            try:
                value = validate_positive_number(request.form.get(f"supply_value_{i}"), "Supply value")
                weight = validate_positive_number(request.form.get(f"supply_weight_{i}"), "Supply weight")
            except ValueError as e:
                return jsonify({"error": f"Supply {i+1}: {str(e)}"}), 400
            
            # Get category and food type
            category = request.form.get(f"supply_category_{i}", "non-food")
            food_type = request.form.get(f"food_type_{i}", "")
            
            # Apply 10% weight increase for food items
            if category == "food":
                weight = weight * 1.1  # 10% increase for food items
                
            supplies.append({
                "name": name,
                "value": value,
                "weight": weight,
                "category": category,
                "food_type": food_type if category == "food" else None
            })

        # Extract and validate vehicles
        vehicles = []
        vehicle_count = int(request.form.get("vehicle_count", 0))
        
        if vehicle_count == 0:
            return jsonify({"error": "Please add at least one vehicle."}), 400
            
        for i in range(vehicle_count):
            name = request.form.get(f"vehicle_name_{i}")
            if not name:
                return jsonify({"error": f"Vehicle name is required for vehicle {i+1}"}), 400
                
            try:
                capacity = validate_positive_number(request.form.get(f"vehicle_capacity_{i}"), "Vehicle capacity")
            except ValueError as e:
                return jsonify({"error": f"Vehicle {i+1}: {str(e)}"}), 400
                
            vehicles.append({
                "id": i + 1,
                "name": name,
                "capacity": capacity,
                "status": "available"
            })

        # Extract and validate nodes
        nodes = []
        demands = {}
        node_count = int(request.form.get("node_count", 0))
        
        if node_count == 0:
            return jsonify({"error": "Please add at least one location."}), 400
            
        # First pass: collect all node names
        node_names = set()
        for i in range(node_count):
            name = request.form.get(f"node_name_{i}")
            if not name:
                return jsonify({"error": f"Location name is required for node {i+1}"}), 400
            if name in node_names:
                return jsonify({"error": f"Duplicate location name: {name}"}), 400
            node_names.add(name)
            
        # Second pass: validate and create nodes
        has_warehouse = False
        for i in range(node_count):
            name = request.form.get(f"node_name_{i}")
            node_type = request.form.get(f"node_type_{i}")
            
            if not node_type:
                return jsonify({"error": f"Location type is required for {name}"}), 400
                
            try:
                x = validate_positive_number(request.form.get(f"node_x_{i}", 0), f"X coordinate for {name}")
                y = validate_positive_number(request.form.get(f"node_y_{i}", 0), f"Y coordinate for {name}")
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
                
            if node_type == "Warehouse":
                has_warehouse = True
                
            nodes.append({
                "name": name,
                "type": node_type,
                "x": x,
                "y": y
            })
            
            # If it's not a warehouse, check demand items
            if node_type != "Warehouse":
                node_demands = []
                for supply in supplies:
                    supply_name = supply["name"]
                    if request.form.get(f"demand_{i}_{supply_name}") == "on":
                        node_demands.append(supply_name)
                if node_demands:
                    demands[name] = node_demands
                else:
                    demands[name] = [s["name"] for s in supplies]  # Default to all items if none selected
                
        if not has_warehouse:
            return jsonify({"error": "Network must have at least one warehouse."}), 400

        # Extract and validate edges
        edges = []
        edge_count = int(request.form.get("edge_count", 0))
        
        if edge_count == 0:
            return jsonify({"error": "Please add at least one road connection."}), 400
            
        for i in range(edge_count):
            from_node = request.form.get(f"edge_from_{i}")
            to_node = request.form.get(f"edge_to_{i}")
            
            if not from_node or not to_node:
                return jsonify({"error": f"Both start and end locations are required for road {i+1}"}), 400
                
            if from_node not in node_names:
                return jsonify({"error": f"Road {i+1}: Start location '{from_node}' does not exist"}), 400
                
            if to_node not in node_names:
                return jsonify({"error": f"Road {i+1}: End location '{to_node}' does not exist"}), 400
                
            if from_node == to_node:
                return jsonify({"error": f"Road {i+1}: Start and end locations cannot be the same"}), 400
                
            try:
                weight = validate_positive_number(request.form.get(f"edge_weight_{i}"), f"Distance for road {i+1}")
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
                
            edges.append({
                "from": from_node,
                "to": to_node,
                "weight": weight
            })

        # Create and store system instance
        current_system = DisasterReliefSystem(supplies, vehicles, nodes, edges, demands)
        image_filename = current_system.run_simulation(save_img=True)
        
        # Add a small delay to ensure file is written
        time.sleep(0.5)
        
        # Save simulation log
        simulation_data = {
            "supplies": supplies,
            "vehicles": vehicles,
            "nodes": nodes,
            "edges": edges,
            "demands": demands
        }
        save_simulation_log(simulation_data, "custom")
        
        return render_template("graph.html", image=image_filename)

    except ValueError as e:
        return jsonify({
            "error": f"Invalid input: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500

@app.route("/demo/<size>")
def demo(size):
    global current_system
    
    # Select demo data based on size
    demo_data = SMALL_DEMO if size == "small" else LARGE_DEMO
    
    # Create and store system instance
    current_system = DisasterReliefSystem(
        demo_data["supplies"],
        demo_data["vehicles"],
        demo_data["nodes"],
        demo_data["edges"],
        demo_data["demands"]
    )
    
    # Run simulation and get the image filename
    image_filename = current_system.run_simulation(save_img=True)
    
    # Add a small delay to ensure file is written
    time.sleep(0.5)
    
    # Save simulation log
    save_simulation_log(demo_data, size)
    
    return render_template("graph.html", image=image_filename)

@app.route('/add_node', methods=['POST'])
def add_node():
    try:
        if not current_system:
            return jsonify({'error': 'No active simulation. Please start a simulation first.'}), 400
            
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        name = data.get('name')
        node_type = data.get('type')
        x = data.get('x')
        y = data.get('y')
        
        # Validate required fields
        if not name:
            return jsonify({'error': 'Node name is required'}), 400
        if not node_type:
            return jsonify({'error': 'Node type is required'}), 400
            
        # Validate coordinates
        try:
            x = float(x) if x is not None else 0
            y = float(y) if y is not None else 0
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid coordinates. X and Y must be numbers.'}), 400
            
        success = current_system.add_new_node(name, node_type, x, y)
        if success['success']:
            return jsonify({
                'message': f'Node {name} added successfully',
                'image': success['image_filename']
            })
        else:
            return jsonify({'error': 'Failed to add node. Please check the node name and type.'}), 400
            
    except Exception as e:
        print(f"Error in add_node: {str(e)}")  # Debug print
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/delete_node', methods=['POST'])
def delete_node():
    try:
        data = request.json
        name = data.get('name')
        
        if not name:
            return jsonify({'error': 'Node name is required'}), 400
            
        success = current_system.delete_node(name)
        if success['success']:
            return jsonify({
                'message': f'Node {name} deleted successfully',
                'image': success['image_filename']
            })
        else:
            return jsonify({'error': 'Failed to delete node'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_warehouse_supplies', methods=['POST'])
def add_warehouse_supplies():
    try:
        data = request.json
        warehouse_name = data.get('warehouse_name')
        new_supplies = data.get('supplies', [])
        
        print(f"Adding supplies to warehouse {warehouse_name}: {new_supplies}")  # Debug print
        
        if not warehouse_name or not new_supplies:
            return jsonify({'error': 'Warehouse name and supplies are required'}), 400
            
        if not current_system:
            return jsonify({'error': 'No active simulation'}), 400
            
        result = current_system.add_warehouse_supplies(warehouse_name, new_supplies)
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Failed to add warehouse supplies')}), 400
            
        response = {
            'message': f'Supplies added to warehouse {warehouse_name}',
            'image': result['image_filename']
        }
        
        # Add success message if present
        if 'message' in result:
            response['success_message'] = result['message']
            
        return jsonify(response)
            
    except Exception as e:
        print(f"Error adding warehouse supplies: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

@app.route('/update_supplies', methods=['POST'])
def update_supplies():
    try:
        data = request.json
        name = data.get('name')
        new_supplies = data.get('supplies', [])
        
        print(f"Updating supplies for {name}: {new_supplies}")  # Debug print
        
        if not name or not new_supplies:
            return jsonify({'error': 'Node name and supplies are required'}), 400
            
        if not current_system:
            return jsonify({'error': 'No active simulation'}), 400
            
        result = current_system.update_node_supplies(name, new_supplies)
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Failed to update supplies')}), 400
            
        response = {
            'message': f'Supplies updated for node {name}',
            'image': result['image_filename']
        }
        
        # Add warning if present
        if 'warning' in result:
            response['warning'] = result['warning']
            response['vehicles_needed'] = result.get('vehicles_needed', 0)
            
        return jsonify(response)
            
    except Exception as e:
        print(f"Error updating supplies: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

@app.route('/connect_nodes', methods=['POST'])
def connect_nodes():
    try:
        data = request.json
        from_node = data.get('from')
        to_node = data.get('to')
        weight = float(data.get('weight', 1.0))
        
        if not all([from_node, to_node]):
            return jsonify({'error': 'Both nodes are required'}), 400
            
        success = current_system.connect_new_node(from_node, to_node, weight)
        if success['success']:
            return jsonify({
                'message': f'Connected {from_node} to {to_node}',
                'image': success['image_filename']
            })
        else:
            return jsonify({'error': 'Failed to connect nodes'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    try:
        data = request.json
        name = data.get('name')
        capacity = data.get('capacity')
        
        if not name or not capacity:
            return jsonify({'error': 'Vehicle name and capacity are required'}), 400
            
        if not current_system:
            return jsonify({'error': 'No active simulation'}), 400
            
        # Add new vehicle
        new_vehicle = {
            "id": len(current_system.original_vehicles) + 1,
            "name": name,
            "capacity": float(capacity),
            "status": "available"
        }
        
        # Add to both original and current vehicles
        current_system.original_vehicles.append(new_vehicle)
        current_system.vehicles.append(new_vehicle.copy())
        
        # Rerun simulation and get the actual filename
        image_filename = current_system.run_simulation(save_img=True)
        
        return jsonify({
            'message': f'Vehicle {name} added successfully',
            'image': image_filename,
            'vehicle_count': len(current_system.original_vehicles)
        })
        
    except Exception as e:
        print(f"Error adding vehicle: {str(e)}")
        return jsonify({'error': str(e)}), 500

def save_simulation_log(simulation_data, simulation_type="custom"):
    """Save simulation data to a log file."""
    try:
        # Generate unique ID for this simulation
        simulation_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create log entry
        log_entry = {
            "id": simulation_id,
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "type": simulation_type,
            "data": simulation_data,
            "graph_image": f"simulation_output_{timestamp}.png"
        }
        
        # Save to JSON file
        log_filename = f"simulation_{timestamp}_{simulation_id[:8]}.json"
        log_path = os.path.join(app.config['LOGS_FOLDER'], log_filename)
        
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        print(f"Simulation log saved: {log_filename}")
        return log_filename
        
    except Exception as e:
        print(f"Error saving simulation log: {str(e)}")
        return None

def load_simulation_log(log_filename):
    """Load simulation data from a log file."""
    try:
        log_path = os.path.join(app.config['LOGS_FOLDER'], log_filename)
        
        with open(log_path, 'r') as f:
            log_entry = json.load(f)
        
        return log_entry
        
    except Exception as e:
        print(f"Error loading simulation log: {str(e)}")
        return None

def get_all_logs():
    """Get list of all available log files."""
    try:
        logs = []
        for filename in os.listdir(app.config['LOGS_FOLDER']):
            if filename.endswith('.json'):
                log_path = os.path.join(app.config['LOGS_FOLDER'], filename)
                try:
                    with open(log_path, 'r') as f:
                        log_data = json.load(f)
                    logs.append({
                        "filename": filename,
                        "timestamp": log_data.get("timestamp", ""),
                        "datetime": log_data.get("datetime", ""),
                        "type": log_data.get("type", "unknown"),
                        "id": log_data.get("id", "")
                    })
                except:
                    continue
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs
        
    except Exception as e:
        print(f"Error getting logs: {str(e)}")
        return []

@app.route("/logs", methods=["GET"])
def view_logs():
    """View all available simulation logs."""
    logs = get_all_logs()
    return render_template("logs.html", logs=logs)

@app.route("/load_log/<filename>", methods=["GET"])
def load_log(filename):
    """Load a simulation from a log file."""
    global current_system
    
    log_entry = load_simulation_log(filename)
    if not log_entry:
        return jsonify({"error": "Log file not found or corrupted"}), 404
    
    try:
        # Recreate the system from saved data
        data = log_entry["data"]
        current_system = DisasterReliefSystem(
            data["supplies"],
            data["vehicles"], 
            data["nodes"],
            data["edges"],
            data["demands"]
        )
        
        # Run simulation to regenerate graph and get the actual filename
        image_filename = current_system.run_simulation(save_img=True)
        
        # Add a small delay to ensure file is written
        time.sleep(0.5)
        
        return render_template("graph.html", image=image_filename)
        
    except Exception as e:
        return jsonify({"error": f"Error loading simulation: {str(e)}"}), 500

@app.route("/download_log/<filename>", methods=["GET"])
def download_log(filename):
    """Download a log file."""
    try:
        log_path = os.path.join(app.config['LOGS_FOLDER'], filename)
        return send_file(log_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"error": f"Error downloading log: {str(e)}"}), 500

@app.route("/delete_log/<filename>", methods=["DELETE"])
def delete_log(filename):
    """Delete a log file."""
    try:
        log_path = os.path.join(app.config['LOGS_FOLDER'], filename)
        if os.path.exists(log_path):
            os.remove(log_path)
            return jsonify({"message": "Log file deleted successfully"})
        else:
            return jsonify({"error": "Log file not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Error deleting log: {str(e)}"}), 500

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)

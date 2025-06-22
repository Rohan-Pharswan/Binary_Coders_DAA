# Disaster Relief Management System

A comprehensive system for optimizing disaster relief operations using advanced algorithms and real-time route planning.

## Features

1. **Relief Distribution Optimization**
   - Efficient transport of food, water, and medicine
   - Priority-based supply allocation
   - Multi-vehicle scheduling

2. **Route Optimization**
   - Shortest path calculation using Dijkstra's algorithm
   - A* algorithm for heuristic-based routing
   - Minimum Spanning Tree for multi-location deliveries
   - Alternative route suggestions

3. **Dynamic Adaptation**
   - Real-time road condition updates
   - Intelligent rerouting on blockages
   - Priority-based task rescheduling

4. **Resource Management**
   - Knapsack-based supply allocation
   - Vehicle capacity optimization
   - Supply prioritization based on demand

5. **User Interface**
   - Interactive network setup
   - Visual route monitoring
   - Real-time status updates

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd disaster-relief-system
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:5000`

3. Follow the steps in the interface:
   - Enter supply information
   - Add vehicle details
   - Define the network (locations and roads)
   - Run the simulation

## System Components

### 1. Graph Representation (`core/graph.py`)
- Network modeling with nodes (locations) and edges (roads)
- Real-time road condition management
- Location type management (warehouses, hospitals, affected areas)

### 2. Route Planning (`core/routing.py`)
- Dijkstra's algorithm for shortest paths
- A* algorithm with heuristic-based routing
- Multi-stop route optimization
- Alternative route finding

### 3. Supply Allocation (`core/knapsack.py`)
- 0/1 knapsack algorithm for optimal loading
- Multi-vehicle supply distribution
- Priority-based allocation
- Load optimization with constraints

### 4. Vehicle Scheduling (`core/scheduler.py`)
- Earliest Deadline First (EDF) scheduling
- Priority-based task assignment
- Real-time schedule updates
- Vehicle status management

### 5. Main System (`core/system.py`)
- Component integration
- Simulation management
- Visualization
- Real-time updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NetworkX library for graph operations
- Flask for web interface
- Matplotlib for visualization 
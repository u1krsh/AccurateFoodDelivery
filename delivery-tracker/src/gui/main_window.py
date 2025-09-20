import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
from datetime import datetime
import sys
import os


# Add parent directory to path to import our models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from models.delivery import Delivery
from models.driver import Driver
from models.graph import Graph
from algorithms.routing import Routing
from utils.image_map_creator import create_image_map

class DeliveryTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Delivery Tracker System")
        self.root.geometry("1200x800")
        
        # Initialize data structures
        self.graph = Graph()
        self.drivers = {}
        self.deliveries = {}
        self.routing = Routing(self.graph)
        
        # Coordinate system variables
        self.show_coordinates = tk.BooleanVar(value=True)
        self.grid_size = 50
        self.canvas_click_enabled = tk.BooleanVar(value=False)
        self.pending_intersection_name = None
        
        # Create GUI elements
        self.create_widgets()
        self.create_sample_data()
        
    def create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_map_tab()
        self.create_drivers_tab()
        self.create_deliveries_tab()
        self.create_routing_tab()
        self.create_tracking_tab()
        
    def create_map_tab(self):
        # Map Management Tab
        self.map_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.map_frame, text="Map Management")
        
        # Map canvas with coordinate system
        canvas_frame = ttk.LabelFrame(self.map_frame, text="Map View")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas with scrollbars
        canvas_container = ttk.Frame(canvas_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.map_canvas = tk.Canvas(canvas_container, bg='white', width=800, height=500,
                                   scrollregion=(0, 0, 1000, 800))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.map_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL, command=self.map_canvas.xview)
        
        self.map_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack canvas and scrollbars
        self.map_canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Bind canvas events
        self.map_canvas.bind("<Button-1>", self.on_canvas_click)
        self.map_canvas.bind("<Motion>", self.on_canvas_motion)
        
        # Coordinate display
        coord_frame = ttk.Frame(canvas_frame)
        coord_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.coord_label = ttk.Label(coord_frame, text="Mouse: (0, 0)")
        self.coord_label.pack(side=tk.LEFT)
        
        ttk.Checkbutton(coord_frame, text="Show Grid", 
                       variable=self.show_coordinates, 
                       command=self.draw_graph).pack(side=tk.RIGHT, padx=5)
        
        # Map controls
        controls_frame = ttk.LabelFrame(self.map_frame, text="Map Controls")
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # First row of controls
        controls_row1 = ttk.Frame(controls_frame)
        controls_row1.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(controls_row1, text="Add Intersection", 
                  command=self.add_intersection).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_row1, text="Click to Add", 
                  command=self.toggle_click_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_row1, text="Add Road", 
                  command=self.add_road).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_row1, text="Clear Map", 
                  command=self.clear_map).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_row1, text="Real Scale View", 
                  command=self.show_real_scale_view).pack(side=tk.LEFT, padx=5)
        
        # Second row of controls
        controls_row2 = ttk.Frame(controls_frame)
        controls_row2.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(controls_row2, text="Quick Add:").pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_row2, text="Grid 3x3", 
                  command=lambda: self.create_grid(3, 3)).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_row2, text="Grid 4x4", 
                  command=lambda: self.create_grid(4, 4)).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_row2, text="Linear 5", 
                  command=lambda: self.create_linear(5)).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_row2, text="Create from Image", 
                  command=self.open_image_map_creator).pack(side=tk.LEFT, padx=5)
        
        # Coordinate helper
        coord_helper_frame = ttk.LabelFrame(self.map_frame, text="Coordinate Helper")
        coord_helper_frame.pack(fill=tk.X, padx=10, pady=5)
        
        helper_row = ttk.Frame(coord_helper_frame)
        helper_row.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(helper_row, text="Common coordinates:").pack(side=tk.LEFT)
        
        common_coords = [
            ("Top-Left", 100, 100), ("Top-Center", 400, 100), ("Top-Right", 700, 100),
            ("Mid-Left", 100, 300), ("Center", 400, 300), ("Mid-Right", 700, 300),
            ("Bot-Left", 100, 500), ("Bot-Center", 400, 500), ("Bot-Right", 700, 500)
        ]
        
        for name, x, y in common_coords:
            btn = ttk.Button(helper_row, text=f"{name}\n({x},{y})", 
                           command=lambda x=x, y=y: self.quick_add_intersection(x, y))
            btn.pack(side=tk.LEFT, padx=2)
    
    def create_drivers_tab(self):
        # Drivers Tab
        self.drivers_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.drivers_frame, text="Drivers")
        
        # Drivers list
        list_frame = ttk.LabelFrame(self.drivers_frame, text="Active Drivers")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for drivers
        columns = ("ID", "Name", "Status", "Current Location", "Deliveries")
        self.drivers_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.drivers_tree.heading(col, text=col)
            self.drivers_tree.column(col, width=150)
            
        self.drivers_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Driver controls
        controls_frame = ttk.Frame(self.drivers_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Add Driver", 
                  command=self.add_driver).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Update Location", 
                  command=self.update_driver_location).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Assign Delivery", 
                  command=self.assign_delivery).pack(side=tk.LEFT, padx=5)
        
    def create_deliveries_tab(self):
        # Deliveries Tab
        self.deliveries_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.deliveries_frame, text="Deliveries")
        
        # Deliveries list
        list_frame = ttk.LabelFrame(self.deliveries_frame, text="Delivery Orders")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for deliveries
        columns = ("ID", "Destination", "Status", "Progress", "Assigned Driver", "Created")
        self.deliveries_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.deliveries_tree.heading(col, text=col)
            self.deliveries_tree.column(col, width=120)
            
        self.deliveries_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Delivery controls
        controls_frame = ttk.Frame(self.deliveries_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="New Delivery", 
                  command=self.create_delivery).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Update Status", 
                  command=self.update_delivery_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Update Progress", 
                  command=self.update_delivery_progress).pack(side=tk.LEFT, padx=5)
        
    def create_routing_tab(self):
        # Routing Tab
        self.routing_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.routing_frame, text="Route Planning")
        
        # Route planning controls
        planning_frame = ttk.LabelFrame(self.routing_frame, text="Route Planning")
        planning_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Source and destination selection
        ttk.Label(planning_frame, text="Start Location:").grid(row=0, column=0, padx=5, pady=5)
        self.start_var = tk.StringVar()
        self.start_combo = ttk.Combobox(planning_frame, textvariable=self.start_var, width=20)
        self.start_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(planning_frame, text="End Location:").grid(row=0, column=2, padx=5, pady=5)
        self.end_var = tk.StringVar()
        self.end_combo = ttk.Combobox(planning_frame, textvariable=self.end_var, width=20)
        self.end_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Algorithm selection
        ttk.Label(planning_frame, text="Algorithm:").grid(row=1, column=0, padx=5, pady=5)
        self.algorithm_var = tk.StringVar(value="BFS")
        algorithm_combo = ttk.Combobox(planning_frame, textvariable=self.algorithm_var, 
                                     values=["BFS", "DFS", "Shortest Path"], width=15)
        algorithm_combo.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(planning_frame, text="Find Route", 
                  command=self.find_route).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(planning_frame, text="Optimize All Routes", 
                  command=self.optimize_routes).grid(row=1, column=3, padx=5, pady=5)
        
        # Route results
        results_frame = ttk.LabelFrame(self.routing_frame, text="Route Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.route_text = tk.Text(results_frame, height=20, wrap=tk.WORD)
        route_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.route_text.yview)
        self.route_text.configure(yscrollcommand=route_scrollbar.set)
        
        self.route_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        route_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_tracking_tab(self):
        # Real-time Tracking Tab
        self.tracking_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tracking_frame, text="Live Tracking")
        
        # Status dashboard
        dashboard_frame = ttk.LabelFrame(self.tracking_frame, text="System Dashboard")
        dashboard_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Statistics
        self.stats_frame = ttk.Frame(dashboard_frame)
        self.stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.total_drivers_label = ttk.Label(self.stats_frame, text="Total Drivers: 0")
        self.total_drivers_label.grid(row=0, column=0, padx=20)
        
        self.active_deliveries_label = ttk.Label(self.stats_frame, text="Active Deliveries: 0")
        self.active_deliveries_label.grid(row=0, column=1, padx=20)
        
        self.completed_deliveries_label = ttk.Label(self.stats_frame, text="Completed: 0")
        self.completed_deliveries_label.grid(row=0, column=2, padx=20)
        
        # Live updates
        updates_frame = ttk.LabelFrame(self.tracking_frame, text="Live Updates")
        updates_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.updates_text = tk.Text(updates_frame, height=25, wrap=tk.WORD)
        updates_scrollbar = ttk.Scrollbar(updates_frame, orient=tk.VERTICAL, command=self.updates_text.yview)
        self.updates_text.configure(yscrollcommand=updates_scrollbar.set)
        
        self.updates_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        updates_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons
        control_frame = ttk.Frame(self.tracking_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.tracking_active = tk.BooleanVar()
        ttk.Checkbutton(control_frame, text="Real-time Tracking", 
                       variable=self.tracking_active, 
                       command=self.toggle_tracking).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Refresh", 
                  command=self.refresh_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
    
    def on_canvas_click(self, event):
        """Handle canvas click events"""
        if self.canvas_click_enabled.get():
            x = self.map_canvas.canvasx(event.x)
            y = self.map_canvas.canvasy(event.y)
            
            # Snap to grid
            x = round(x / self.grid_size) * self.grid_size
            y = round(y / self.grid_size) * self.grid_size
            
            self.add_intersection_at_coordinates(x, y)
    
    def on_canvas_motion(self, event):
        """Update coordinate display on mouse movement"""
        x = self.map_canvas.canvasx(event.x)
        y = self.map_canvas.canvasy(event.y)
        self.coord_label.config(text=f"Mouse: ({int(x)}, {int(y)})")
    
    def toggle_click_mode(self):
        """Toggle click-to-add mode"""
        self.canvas_click_enabled.set(not self.canvas_click_enabled.get())
        mode = "ON" if self.canvas_click_enabled.get() else "OFF"
        self.log_update(f"Click-to-add mode: {mode}")
        
        # Change cursor to indicate mode
        if self.canvas_click_enabled.get():
            self.map_canvas.config(cursor="crosshair")
        else:
            self.map_canvas.config(cursor="")
    
    def add_intersection_at_coordinates(self, x, y):
        """Add intersection at specific coordinates"""
        node_id = simpledialog.askstring("Add Intersection", 
                                       f"Enter intersection ID for position ({int(x)}, {int(y)}):")
        if node_id and node_id not in self.graph.nodes:
            self.graph.add_node(node_id, {"x": x, "y": y})
            self.routing = Routing(self.graph)
            self.update_location_combos()
            self.draw_graph()
            self.log_update(f"Added intersection {node_id} at ({int(x)}, {int(y)})")
    
    def quick_add_intersection(self, x, y):
        """Quick add intersection with preset coordinates"""
        node_id = simpledialog.askstring("Add Intersection", 
                                       f"Enter intersection ID for position ({x}, {y}):")
        if node_id and node_id not in self.graph.nodes:
            self.graph.add_node(node_id, {"x": x, "y": y})
            self.routing = Routing(self.graph)
            self.update_location_combos()
            self.draw_graph()
            self.log_update(f"Added intersection {node_id} at ({x}, {y})")
    
    def create_grid(self, rows, cols):
        """Create a grid of intersections"""
        start_x, start_y = 100, 100
        spacing_x, spacing_y = 150, 150
        
        nodes_added = []
        
        for row in range(rows):
            for col in range(cols):
                node_id = f"G{row+1}{col+1}"
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                
                if node_id not in self.graph.nodes:
                    self.graph.add_node(node_id, {"x": x, "y": y})
                    nodes_added.append(node_id)
        
        # Add horizontal connections
        for row in range(rows):
            for col in range(cols - 1):
                node1 = f"G{row+1}{col+1}"
                node2 = f"G{row+1}{col+2}"
                if not self.graph.has_edge(node1, node2):
                    self.graph.add_edge(node1, node2, 5)  # Default weight
        
        # Add vertical connections
        for row in range(rows - 1):
            for col in range(cols):
                node1 = f"G{row+1}{col+1}"
                node2 = f"G{row+2}{col+1}"
                if not self.graph.has_edge(node1, node2):
                    self.graph.add_edge(node1, node2, 5)  # Default weight
        
        self.routing = Routing(self.graph)
        self.update_location_combos()
        self.draw_graph()
        self.log_update(f"Created {rows}x{cols} grid with {len(nodes_added)} new intersections")
    
    def create_linear(self, count):
        """Create a linear chain of intersections"""
        start_x, start_y = 100, 300
        spacing = 120
        
        nodes_added = []
        
        for i in range(count):
            node_id = f"L{i+1}"
            x = start_x + i * spacing
            y = start_y
            
            if node_id not in self.graph.nodes:
                self.graph.add_node(node_id, {"x": x, "y": y})
                nodes_added.append(node_id)
        
        # Connect adjacent nodes
        for i in range(count - 1):
            node1 = f"L{i+1}"
            node2 = f"L{i+2}"
            if not self.graph.has_edge(node1, node2):
                self.graph.add_edge(node1, node2, 4)  # Default weight
        
        self.routing = Routing(self.graph)
        self.update_location_combos()
        self.draw_graph()
        self.log_update(f"Created linear chain with {len(nodes_added)} new intersections")
    
    def create_sample_data(self):
        # Create sample intersections
        intersections = [
            ("A", 100, 100), ("B", 300, 100), ("C", 500, 100),
            ("D", 100, 300), ("E", 300, 300), ("F", 500, 300),
            ("G", 100, 500), ("H", 300, 500), ("I", 500, 500)
        ]
        
        for node_id, x, y in intersections:
            self.graph.add_node(node_id, {"x": x, "y": y})
        
        # Create sample roads with time weights
        roads = [
            ("A", "B", 5), ("B", "C", 7), ("A", "D", 6),
            ("B", "E", 4), ("C", "F", 3), ("D", "E", 8),
            ("E", "F", 5), ("D", "G", 9), ("E", "H", 6),
            ("F", "I", 4), ("G", "H", 7), ("H", "I", 5)
        ]
        
        for start, end, weight in roads:
            self.graph.add_edge(start, end, weight)
        
        # Recreate routing with updated graph
        self.routing = Routing(self.graph)
        
        # Update combo boxes
        self.update_location_combos()
        self.draw_graph()
        
        # Add sample drivers
        self.drivers["D001"] = Driver("D001", "John Doe", "A")
        self.drivers["D002"] = Driver("D002", "Jane Smith", "E")
        
        # Add sample deliveries
        self.deliveries["DEL001"] = Delivery("DEL001", "C")
        self.deliveries["DEL002"] = Delivery("DEL002", "I")
        
        self.refresh_all_displays()
    
    def add_intersection(self):
        # Show coordinate helper dialog
        coord_dialog = CoordinateDialog(self.root, self.graph.nodes)
        if coord_dialog.result:
            node_id, x, y = coord_dialog.result
            if node_id not in self.graph.nodes:
                self.graph.add_node(node_id, {"x": x, "y": y})
                self.routing = Routing(self.graph)
                self.update_location_combos()
                self.draw_graph()
                self.log_update(f"Added intersection {node_id} at ({x}, {y})")
    
    def add_road(self):
        nodes = list(self.graph.nodes.keys())
        if len(nodes) < 2:
            messagebox.showwarning("Warning", "Need at least 2 intersections to add a road")
            return
        
        # Create road dialog
        road_dialog = RoadDialog(self.root, nodes)
        if road_dialog.result:
            start, end, weight = road_dialog.result
            if start != end:
                self.graph.add_edge(start, end, weight)
                self.routing = Routing(self.graph)
                self.draw_graph()
                self.log_update(f"Added road from {start} to {end} (time: {weight} min)")
    
    def clear_map(self):
        self.graph = Graph()
        self.routing = Routing(self.graph)
        self.map_canvas.delete("all")
        self.update_location_combos()
        self.draw_graph()
        self.log_update("Map cleared")
    
    def draw_graph(self):
        self.map_canvas.delete("all")
        
        # Draw coordinate grid if enabled
        if self.show_coordinates.get():
            self.draw_coordinate_grid()
        
        # Draw edges first
        for node1 in self.graph.edges:
            for node2, weight in self.graph.edges[node1].items():
                x1, y1 = self.graph.nodes[node1]["x"], self.graph.nodes[node1]["y"]
                x2, y2 = self.graph.nodes[node2]["x"], self.graph.nodes[node2]["y"]
                
                # Draw line
                self.map_canvas.create_line(x1, y1, x2, y2, width=2, fill="blue")
                
                # Draw weight label
                mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
                self.map_canvas.create_text(mid_x, mid_y, text=str(weight), 
                                          fill="red", font=("Arial", 8), 
                                          tags="weight")
        
        # Draw nodes
        for node_id, data in self.graph.nodes.items():
            x, y = data["x"], data["y"]
            # Draw circle for intersection
            self.map_canvas.create_oval(x-15, y-15, x+15, y+15, 
                                      fill="yellow", outline="black", width=2,
                                      tags="node")
            # Draw label
            self.map_canvas.create_text(x, y, text=node_id, font=("Arial", 10, "bold"),
                                      tags="node_label")
            # Draw coordinates
            self.map_canvas.create_text(x, y-25, text=f"({int(x)},{int(y)})", 
                                      font=("Arial", 7), fill="gray",
                                      tags="coordinates")
    
    def draw_coordinate_grid(self):
        """Draw coordinate grid on canvas"""
        # Get canvas dimensions
        canvas_width = 1000
        canvas_height = 800
        
        # Draw vertical lines
        for x in range(0, canvas_width, self.grid_size):
            self.map_canvas.create_line(x, 0, x, canvas_height, 
                                      fill="lightgray", width=1, tags="grid")
            if x % (self.grid_size * 2) == 0:  # Label every other line
                self.map_canvas.create_text(x, 10, text=str(x), 
                                          fill="gray", font=("Arial", 8), tags="grid_label")
        
        # Draw horizontal lines
        for y in range(0, canvas_height, self.grid_size):
            self.map_canvas.create_line(0, y, canvas_width, y, 
                                      fill="lightgray", width=1, tags="grid")
            if y % (self.grid_size * 2) == 0:  # Label every other line
                self.map_canvas.create_text(10, y, text=str(y), 
                                          fill="gray", font=("Arial", 8), tags="grid_label")
    
    def add_driver(self):
        driver_id = simpledialog.askstring("Add Driver", "Enter driver ID:")
        if driver_id and driver_id not in self.drivers:
            name = simpledialog.askstring("Driver Name", "Enter driver name:")
            nodes = list(self.graph.nodes.keys())
            if nodes:
                location = simpledialog.askstring("Location", f"Enter current location ({', '.join(nodes)}):")
                if location in nodes and name:
                    self.drivers[driver_id] = Driver(driver_id, name, location)
                    self.refresh_drivers_display()
                    self.log_update(f"Added driver {name} (ID: {driver_id}) at {location}")
    
    def update_driver_location(self):
        selection = self.drivers_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a driver")
            return
            
        item = self.drivers_tree.item(selection[0])
        driver_id = item['values'][0]
        
        nodes = list(self.graph.nodes.keys())
        location = simpledialog.askstring("Update Location", 
                                        f"New location ({', '.join(nodes)}):")
        
        if location in nodes:
            self.drivers[driver_id].update_location(location)
            self.refresh_drivers_display()
            self.log_update(f"Driver {driver_id} moved to {location}")
    
    def create_delivery(self):
        delivery_id = simpledialog.askstring("New Delivery", "Enter delivery ID:")
        if delivery_id and delivery_id not in self.deliveries:
            nodes = list(self.graph.nodes.keys())
            destination = simpledialog.askstring("Destination", 
                                               f"Enter destination ({', '.join(nodes)}):")
            if destination in nodes:
                self.deliveries[delivery_id] = Delivery(delivery_id, destination)
                self.refresh_deliveries_display()
                self.log_update(f"Created delivery {delivery_id} to {destination}")
    
    def assign_delivery(self):
        driver_selection = self.drivers_tree.selection()
        if not driver_selection:
            messagebox.showwarning("Warning", "Please select a driver")
            return
            
        driver_item = self.drivers_tree.item(driver_selection[0])
        driver_id = driver_item['values'][0]
        
        # Show available deliveries
        available_deliveries = [d_id for d_id, delivery in self.deliveries.items() 
                              if delivery.status == "Pending"]
        
        if not available_deliveries:
            messagebox.showinfo("Info", "No pending deliveries available")
            return
            
        delivery_id = simpledialog.askstring("Assign Delivery", 
                                           f"Select delivery ID ({', '.join(available_deliveries)}):")
        
        if delivery_id in available_deliveries:
            self.drivers[driver_id].assign_delivery(delivery_id)
            self.deliveries[delivery_id].update_status("Assigned")
            self.refresh_all_displays()
            self.log_update(f"Assigned delivery {delivery_id} to driver {driver_id}")
    
    def update_delivery_status(self):
        selection = self.deliveries_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a delivery")
            return
            
        item = self.deliveries_tree.item(selection[0])
        delivery_id = item['values'][0]
        
        statuses = ["Pending", "Assigned", "In Transit", "Delivered", "Completed"]
        status = simpledialog.askstring("Update Status", 
                                      f"New status ({', '.join(statuses)}):")
        
        if status in statuses:
            self.deliveries[delivery_id].update_status(status)
            self.refresh_deliveries_display()
            self.log_update(f"Delivery {delivery_id} status updated to {status}")
    
    def update_delivery_progress(self):
        selection = self.deliveries_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a delivery")
            return
            
        item = self.deliveries_tree.item(selection[0])
        delivery_id = item['values'][0]
        
        progress = simpledialog.askinteger("Update Progress", 
                                         "Progress increment (0-100):", 
                                         minvalue=0, maxvalue=100)
        
        if progress is not None:
            self.deliveries[delivery_id].update_progress(progress)
            self.refresh_deliveries_display()
            self.log_update(f"Delivery {delivery_id} progress updated by {progress}%")
    
    def find_route(self):
        start = self.start_var.get()
        end = self.end_var.get()
        algorithm = self.algorithm_var.get()
        
        if not start or not end:
            messagebox.showwarning("Warning", "Please select start and end locations")
            return
            
        if start not in self.graph.nodes or end not in self.graph.nodes:
            messagebox.showerror("Error", "Invalid start or end location")
            return
        
        try:
            if algorithm == "BFS":
                path = self.routing.find_shortest_path_bfs(start, end)
            elif algorithm == "DFS":
                path = self.routing.find_shortest_path_dfs(start, end)
            else:  # Shortest Path
                path = self.routing.shortest_path(start, end)
            
            if path:
                total_time = self.routing.calculate_route_time(path)
                result = f"\n{algorithm} Route from {start} to {end}:\n"
                result += f"Path: {' -> '.join(path)}\n"
                result += f"Total Time: {total_time} minutes\n"
                result += f"Number of intersections: {len(path)}\n"
                result += "-" * 50 + "\n"
                
                self.route_text.insert(tk.END, result)
                self.route_text.see(tk.END)
                self.log_update(f"Found {algorithm} route from {start} to {end}")
            else:
                messagebox.showwarning("Warning", f"No route found from {start} to {end}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Route calculation failed: {str(e)}")
    
    def optimize_routes(self):
        result = "\nRoute Optimization Results:\n"
        result += "=" * 50 + "\n"
        
        active_deliveries = [(d_id, d) for d_id, d in self.deliveries.items() 
                           if d.status in ["Assigned", "In Transit"]]
        
        if not active_deliveries:
            result += "No active deliveries to optimize.\n"
        else:
            for delivery_id, delivery in active_deliveries:
                # Find assigned driver
                assigned_driver = None
                for driver_id, driver in self.drivers.items():
                    if delivery_id in driver.assigned_deliveries:
                        assigned_driver = driver
                        break
                
                if assigned_driver:
                    try:
                        path = self.routing.shortest_path(assigned_driver.current_location, 
                                                        delivery.destination)
                        if path:
                            total_time = self.routing.calculate_route_time(path)
                            result += f"\nDelivery {delivery_id}:\n"
                            result += f"Driver: {assigned_driver.name} (at {assigned_driver.current_location})\n"
                            result += f"Destination: {delivery.destination}\n"
                            result += f"Optimal path: {' -> '.join(path)}\n"
                            result += f"Estimated time: {total_time} minutes\n"
                    except:
                        result += f"\nDelivery {delivery_id}: Route calculation failed\n"
        
        result += "\n" + "=" * 50 + "\n"
        self.route_text.insert(tk.END, result)
        self.route_text.see(tk.END)
        self.log_update("Optimized all active delivery routes")
    
    def toggle_tracking(self):
        if self.tracking_active.get():
            self.start_live_tracking()
        else:
            self.stop_live_tracking()
    
    def start_live_tracking(self):
        self.log_update("Live tracking started")
        self.tracking_thread = threading.Thread(target=self.live_tracking_loop, daemon=True)
        self.tracking_thread.start()
    
    def stop_live_tracking(self):
        self.log_update("Live tracking stopped")
    
    def live_tracking_loop(self):
        while self.tracking_active.get():
            # Simulate some updates
            time.sleep(5)  # Update every 5 seconds
            if self.tracking_active.get():
                self.root.after(0, self.simulate_updates)
    
    def simulate_updates(self):
        # Simulate random delivery progress updates
        import random
        
        active_deliveries = [(d_id, d) for d_id, d in self.deliveries.items() 
                           if d.status in ["Assigned", "In Transit"]]
        
        if active_deliveries:
            delivery_id, delivery = random.choice(active_deliveries)
            if delivery.progress < 100:
                progress_increment = random.randint(5, 15)
                delivery.update_progress(progress_increment)
                self.refresh_deliveries_display()
                self.log_update(f"Auto-update: Delivery {delivery_id} progress +{progress_increment}%")
    
    def refresh_data(self):
        self.refresh_all_displays()
        self.log_update("Data refreshed")
    
    def refresh_all_displays(self):
        self.refresh_drivers_display()
        self.refresh_deliveries_display()
        self.update_statistics()
    
    def refresh_drivers_display(self):
        for item in self.drivers_tree.get_children():
            self.drivers_tree.delete(item)
            
        for driver_id, driver in self.drivers.items():
            deliveries_count = len(driver.assigned_deliveries)
            self.drivers_tree.insert("", tk.END, values=(
                driver_id, driver.name, driver.status, 
                driver.current_location, deliveries_count
            ))
    
    def refresh_deliveries_display(self):
        for item in self.deliveries_tree.get_children():
            self.deliveries_tree.delete(item)
            
        for delivery_id, delivery in self.deliveries.items():
            # Find assigned driver
            assigned_driver = "None"
            for driver_id, driver in self.drivers.items():
                if delivery_id in driver.assigned_deliveries:
                    assigned_driver = driver.name
                    break
            
            self.deliveries_tree.insert("", tk.END, values=(
                delivery_id, delivery.destination, delivery.status,
                f"{delivery.progress}%", assigned_driver,
                datetime.now().strftime("%H:%M")
            ))
    
    def update_statistics(self):
        total_drivers = len(self.drivers)
        active_deliveries = len([d for d in self.deliveries.values() 
                               if d.status in ["Assigned", "In Transit"]])
        completed_deliveries = len([d for d in self.deliveries.values() 
                                  if d.status == "Completed"])
        
        self.total_drivers_label.config(text=f"Total Drivers: {total_drivers}")
        self.active_deliveries_label.config(text=f"Active Deliveries: {active_deliveries}")
        self.completed_deliveries_label.config(text=f"Completed: {completed_deliveries}")
    
    def update_location_combos(self):
        nodes = list(self.graph.nodes.keys())
        self.start_combo['values'] = nodes
        self.end_combo['values'] = nodes
    
    def log_update(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.updates_text.insert(tk.END, log_entry)
        self.updates_text.see(tk.END)
    
    def clear_log(self):
        self.updates_text.delete(1.0, tk.END)
        self.log_update("Log cleared")
    
    def open_image_map_creator(self):
        """Open the image-based map creator"""
        try:
            create_image_map(parent_gui=self)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image map creator: {str(e)}")
    
    def show_real_scale_view(self):
        """Show graph with real proportional distances"""
        if not self.graph.nodes:
            messagebox.showwarning("Warning", "No graph to display")
            return
        
        # Create new window for real scale view
        scale_window = tk.Toplevel(self.root)
        scale_window.title("Real Scale Proportional View")
        scale_window.geometry("1000x700")
        
        # Create canvas
        canvas = tk.Canvas(scale_window, bg='white')
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Calculate proportional positions
        self.draw_proportional_graph(canvas)

    def draw_proportional_graph(self, canvas):
        """Draw graph with real proportional distances"""
        if not self.graph.nodes:
            return
        
        # Get all nodes and their positions
        nodes = list(self.graph.nodes.items())
        if len(nodes) < 2:
            canvas.create_text(500, 350, text="Need at least 2 nodes for proportional view", 
                             font=("Arial", 16), fill="red")
            return
        
        # Calculate distances between all node pairs
        distances = {}
        for i, (node1, data1) in enumerate(nodes):
            for j, (node2, data2) in enumerate(nodes):
                if i < j:
                    # Use graph edge weight as real distance, or calculate from coordinates
                    if node1 in self.graph.edges and node2 in self.graph.edges[node1]:
                        real_distance = self.graph.edges[node1][node2]
                    else:
                        # Fallback to coordinate distance (scaled down)
                        dx = data1["x"] - data2["x"]
                        dy = data1["y"] - data2["y"]
                        real_distance = (dx*dx + dy*dy) ** 0.5 / 10  # Scale down
                    
                    distances[(node1, node2)] = real_distance
        
        if not distances:
            canvas.create_text(500, 350, text="No connections found", 
                             font=("Arial", 16), fill="red")
            return
        
        # Use multidimensional scaling (simplified version)
        # Start with first node at center
        positions = {}
        first_node = nodes[0][0]
        positions[first_node] = (500, 350)  # Center of canvas
        
        # Place second node
        if len(nodes) > 1:
            second_node = nodes[1][0]
            distance_key = (first_node, second_node) if (first_node, second_node) in distances else (second_node, first_node)
            if distance_key in distances:
                scale_factor = 3  # Pixels per distance unit
                dist = distances[distance_key] * scale_factor
                positions[second_node] = (500 + dist, 350)
            else:
                positions[second_node] = (600, 350)
        
        # Place remaining nodes using triangulation (simplified)
        for node, _ in nodes[2:]:
            # Find best position based on distances to already placed nodes
            best_pos = None
            min_error = float('inf')
            
            # Try multiple positions and find the one with minimum distance error
            for test_x in range(100, 900, 50):
                for test_y in range(100, 600, 50):
                    error = 0
                    valid = True
                    
                    for placed_node, (px, py) in positions.items():
                        distance_key = (node, placed_node) if (node, placed_node) in distances else (placed_node, node)
                        if distance_key in distances:
                            expected_dist = distances[distance_key] * 3  # Same scale factor
                            actual_dist = ((test_x - px)**2 + (test_y - py)**2) ** 0.5
                            error += abs(expected_dist - actual_dist)
                        else:
                            valid = False
                            break
                    
                    if valid and error < min_error:
                        min_error = error
                        best_pos = (test_x, test_y)
            
            if best_pos:
                positions[node] = best_pos
            else:
                # Fallback position
                angle = len(positions) * 60  # Degrees
                radius = 100
                import math
                x = 500 + radius * math.cos(math.radians(angle))
                y = 350 + radius * math.sin(math.radians(angle))
                positions[node] = (x, y)
        
        # Draw edges with proportional lengths
        for (node1, node2), distance in distances.items():
            if node1 in positions and node2 in positions:
                x1, y1 = positions[node1]
                x2, y2 = positions[node2]
                
                # Calculate actual displayed distance
                actual_distance = ((x2-x1)**2 + (y2-y1)**2) ** 0.5
                
                # Draw edge
                canvas.create_line(x1, y1, x2, y2, width=2, fill="blue")
                
                # Draw distance label
                mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                canvas.create_text(mid_x, mid_y, text=f"{distance:.1f}", 
                                 fill="red", font=("Arial", 8))
        
        # Draw nodes
        for node, (x, y) in positions.items():
            # Draw circle
            canvas.create_oval(x-15, y-15, x+15, y+15, 
                             fill="yellow", outline="black", width=2)
            # Draw label
            canvas.create_text(x, y, text=node, font=("Arial", 10, "bold"))
        
        # Add title and legend
        canvas.create_text(500, 30, text="Real Scale Proportional View", 
                         font=("Arial", 16, "bold"))
        canvas.create_text(500, 50, text="Distances shown are proportional to real travel times/distances", 
                         font=("Arial", 10), fill="gray")
        

class CoordinateDialog:
    def __init__(self, parent, existing_nodes):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Intersection")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Create form
        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Node ID
        ttk.Label(frame, text="Intersection ID:").grid(row=0, column=0, sticky="w", pady=5)
        self.id_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.id_var, width=20).grid(row=0, column=1, pady=5)
        
        # Coordinates
        ttk.Label(frame, text="X Coordinate:").grid(row=1, column=0, sticky="w", pady=5)
        self.x_var = tk.IntVar(value=200)
        x_spinbox = tk.Spinbox(frame, from_=0, to=1000, increment=50, textvariable=self.x_var, width=18)
        x_spinbox.grid(row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Y Coordinate:").grid(row=2, column=0, sticky="w", pady=5)
        self.y_var = tk.IntVar(value=200)
        y_spinbox = tk.Spinbox(frame, from_=0, to=800, increment=50, textvariable=self.y_var, width=18)
        y_spinbox.grid(row=2, column=1, pady=5)
        
        # Quick coordinate buttons
        ttk.Label(frame, text="Quick Coordinates:").grid(row=3, column=0, sticky="w", pady=10)
        
        coord_frame = ttk.Frame(frame)
        coord_frame.grid(row=4, column=0, columnspan=2, pady=5)
        
        quick_coords = [
            ("Top-Left", 100, 100), ("Top-Center", 400, 100), ("Top-Right", 700, 100),
            ("Center", 400, 300), ("Bottom", 400, 500)
        ]
        
        for i, (name, x, y) in enumerate(quick_coords):
            ttk.Button(coord_frame, text=f"{name}\n({x},{y})", 
                      command=lambda x=x, y=y: self.set_coords(x, y)).grid(row=i//3, column=i%3, padx=2, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Focus on ID entry
        self.dialog.after(100, lambda: self.id_var and self.dialog.focus_set())
        
        self.dialog.wait_window()
    
    def set_coords(self, x, y):
        self.x_var.set(x)
        self.y_var.set(y)
    
    def ok_clicked(self):
        node_id = self.id_var.get().strip()
        if node_id:
            self.result = (node_id, self.x_var.get(), self.y_var.get())
            self.dialog.destroy()


class RoadDialog:
    def __init__(self, parent, nodes):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Road")
        self.dialog.geometry("300x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Create form
        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Start node
        ttk.Label(frame, text="Start Intersection:").grid(row=0, column=0, sticky="w", pady=5)
        self.start_var = tk.StringVar()
        start_combo = ttk.Combobox(frame, textvariable=self.start_var, values=nodes, width=18)
        start_combo.grid(row=0, column=1, pady=5)
        
        # End node
        ttk.Label(frame, text="End Intersection:").grid(row=1, column=0, sticky="w", pady=5)
        self.end_var = tk.StringVar()
        end_combo = ttk.Combobox(frame, textvariable=self.end_var, values=nodes, width=18)
        end_combo.grid(row=1, column=1, pady=5)
        
        # Weight
        ttk.Label(frame, text="Travel Time (min):").grid(row=2, column=0, sticky="w", pady=5)
        self.weight_var = tk.DoubleVar(value=5.0)
        weight_spinbox = tk.Spinbox(frame, from_=0.1, to=60.0, increment=0.5, 
                                   textvariable=self.weight_var, width=18)
        weight_spinbox.grid(row=2, column=1, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        self.dialog.wait_window()
    
    def ok_clicked(self):
        start = self.start_var.get()
        end = self.end_var.get()
        weight = self.weight_var.get()
        
        if start and end and start != end:
            self.result = (start, end, weight)
            self.dialog.destroy()


def main():
    root = tk.Tk()
    app = DeliveryTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
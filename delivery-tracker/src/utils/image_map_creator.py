import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from models.graph import Graph
from algorithms.routing import Routing

class ImageMapCreator:
    def __init__(self, parent_gui=None):
        self.parent_gui = parent_gui
        self.root = tk.Toplevel() if parent_gui else tk.Tk()
        self.root.title("Create Map from Image")
        self.root.geometry("1400x900")
        
        # Map data
        self.image_path = None
        self.original_image = None
        self.display_image = None
        self.photo = None
        self.scale_factor = 1.0
        
        # Node and edge data
        self.nodes = {}  # {node_id: {"x": x, "y": y, "real_x": real_x, "real_y": real_y}}
        self.edges = {}  # {node1: {node2: weight}}
        self.temp_nodes = []  # For drawing temporary nodes
        
        # Drawing state
        self.drawing_mode = "node"  # "node", "edge", "measure"
        self.selected_nodes = []  # For edge creation
        self.scale_reference = None  # For real-world scaling
        
        # Real-world scaling
        self.pixels_per_meter = 1.0
        self.real_scale_set = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File controls
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(file_frame, text="Load Image", 
                  command=self.load_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Save Map", 
                  command=self.save_map).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Load Map", 
                  command=self.load_map).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Export to Main", 
                  command=self.export_to_main).pack(side=tk.LEFT, padx=5)
        
        # Drawing mode controls
        mode_frame = ttk.Frame(control_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mode_var = tk.StringVar(value="node")
        ttk.Radiobutton(mode_frame, text="Add Nodes", variable=self.mode_var, 
                       value="node", command=self.change_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Add Edges", variable=self.mode_var, 
                       value="edge", command=self.change_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Set Scale", variable=self.mode_var, 
                       value="measure", command=self.change_mode).pack(side=tk.LEFT, padx=5)
        
        # Scale controls
        scale_frame = ttk.Frame(control_frame)
        scale_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(scale_frame, text="Real Scale:").pack(side=tk.LEFT, padx=5)
        self.scale_label = ttk.Label(scale_frame, text="Not Set", foreground="red")
        self.scale_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(scale_frame, text="Clear All", 
                  command=self.clear_all).pack(side=tk.RIGHT, padx=5)
        ttk.Button(scale_frame, text="Auto-detect Roads", 
                  command=self.auto_detect_roads).pack(side=tk.RIGHT, padx=5)
        
        # Canvas container
        canvas_container = ttk.Frame(main_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas with scrollbars
        self.canvas = tk.Canvas(canvas_container, bg='white', cursor="crosshair")
        
        v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_right_click)  # Right click for context menu
        self.canvas.bind("<Motion>", self.on_mouse_motion)
        
        # Status bar
        self.status_var = tk.StringVar(value="Load an image to start creating your map")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(5, 0))
        
    def load_image(self):
        """Load an image file for map creation"""
        file_path = filedialog.askopenfilename(
            title="Select Map Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.image_path = file_path
                self.original_image = Image.open(file_path)
                
                # Resize image if too large
                max_size = (1200, 800)
                self.original_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                self.display_image = self.original_image.copy()
                self.photo = ImageTk.PhotoImage(self.display_image)
                
                # Update canvas
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo, tags="background")
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                
                self.status_var.set(f"Loaded: {os.path.basename(file_path)} - Click to add intersections")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image: {str(e)}")
    
    def change_mode(self):
        """Change drawing mode"""
        self.drawing_mode = self.mode_var.get()
        self.selected_nodes = []
        
        if self.drawing_mode == "node":
            self.canvas.config(cursor="crosshair")
            self.status_var.set("Node mode: Click to add intersections")
        elif self.drawing_mode == "edge":
            self.canvas.config(cursor="hand2")
            self.status_var.set("Edge mode: Click two nodes to connect them")
        elif self.drawing_mode == "measure":
            self.canvas.config(cursor="sizing")
            self.status_var.set("Scale mode: Click and drag to set real-world scale")
    
    def on_canvas_click(self, event):
        """Handle canvas click events"""
        if not self.original_image:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self.drawing_mode == "node":
            self.add_node_at_position(x, y)
        elif self.drawing_mode == "edge":
            self.handle_edge_click(x, y)
        elif self.drawing_mode == "measure":
            self.handle_scale_click(x, y)
    
    def add_node_at_position(self, x, y):
        """Add a node at the specified position"""
        node_id = simpledialog.askstring("Node ID", "Enter intersection/node ID:")
        if node_id and node_id not in self.nodes:
            # Convert to real-world coordinates if scale is set
            real_x, real_y = self.pixel_to_real(x, y)
            
            self.nodes[node_id] = {
                "x": x, "y": y,
                "real_x": real_x, "real_y": real_y
            }
            
            self.draw_node(node_id, x, y)
            self.status_var.set(f"Added node {node_id} at ({int(x)}, {int(y)})")
    
    def handle_edge_click(self, x, y):
        """Handle clicking in edge mode"""
        # Find closest node
        closest_node = self.find_closest_node(x, y, max_distance=30)
        
        if closest_node:
            if closest_node not in self.selected_nodes:
                self.selected_nodes.append(closest_node)
                self.highlight_node(closest_node, "blue")
                
                if len(self.selected_nodes) == 2:
                    self.create_edge()
        else:
            # Clear selection if clicking empty space
            self.clear_selection()
    
    def handle_scale_click(self, x, y):
        """Handle clicking in scale/measure mode"""
        if not hasattr(self, 'scale_start'):
            # First click - start measuring
            self.scale_start = (x, y)
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="red", tags="scale_temp")
            self.status_var.set("Click second point to complete scale measurement")
            
        else:
            # Second click - complete measurement
            end_x, end_y = x, y
            start_x, start_y = self.scale_start
            
            # Calculate pixel distance
            pixel_distance = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
            
            # Ask for real-world distance
            real_distance = simpledialog.askfloat(
                "Real Distance", 
                f"Enter real-world distance for {pixel_distance:.1f} pixels (in meters):",
                minvalue=0.1
            )
            
            if real_distance:
                self.pixels_per_meter = pixel_distance / real_distance
                self.real_scale_set = True
                self.scale_label.config(text=f"{self.pixels_per_meter:.2f} px/m", foreground="green")
                
                # Draw scale line
                self.canvas.create_line(start_x, start_y, end_x, end_y, 
                                      fill="red", width=3, tags="scale_line")
                self.canvas.create_text((start_x + end_x)/2, (start_y + end_y)/2 - 15,
                                      text=f"{real_distance}m", fill="red", font=("Arial", 10, "bold"))
            
            # Clean up
            self.canvas.delete("scale_temp")
            delattr(self, 'scale_start')
            self.status_var.set("Scale set successfully")
    
    def create_edge(self):
        """Create edge between selected nodes"""
        if len(self.selected_nodes) == 2:
            node1, node2 = self.selected_nodes
            
            # Calculate real-world distance if scale is set
            if self.real_scale_set:
                real_dist = self.calculate_real_distance(node1, node2)
                # Estimate travel time (assuming average speed of 30 km/h = 8.33 m/s)
                travel_time = real_dist / 8.33 / 60  # Convert to minutes
            else:
                travel_time = 5.0  # Default travel time
            
            # Ask user for travel time
            weight = simpledialog.askfloat(
                "Travel Time",
                f"Enter travel time between {node1} and {node2} (minutes):",
                initialvalue=travel_time,
                minvalue=0.1
            )
            
            if weight:
                # Add edge to both nodes (undirected graph)
                if node1 not in self.edges:
                    self.edges[node1] = {}
                if node2 not in self.edges:
                    self.edges[node2] = {}
                
                self.edges[node1][node2] = weight
                self.edges[node2][node1] = weight
                
                self.draw_edge(node1, node2, weight)
                self.status_var.set(f"Connected {node1} to {node2} (time: {weight:.1f} min)")
        
        self.clear_selection()
    
    def calculate_real_distance(self, node1, node2):
        """Calculate real-world distance between two nodes"""
        x1, y1 = self.nodes[node1]["x"], self.nodes[node1]["y"]
        x2, y2 = self.nodes[node2]["x"], self.nodes[node2]["y"]
        
        pixel_distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return pixel_distance / self.pixels_per_meter
    
    def pixel_to_real(self, x, y):
        """Convert pixel coordinates to real-world coordinates"""
        if self.real_scale_set:
            return x / self.pixels_per_meter, y / self.pixels_per_meter
        return x, y
    
    def find_closest_node(self, x, y, max_distance=30):
        """Find the closest node to the given coordinates"""
        closest_node = None
        min_distance = max_distance
        
        for node_id, data in self.nodes.items():
            distance = np.sqrt((data["x"] - x)**2 + (data["y"] - y)**2)
            if distance < min_distance:
                min_distance = distance
                closest_node = node_id
        
        return closest_node
    
    def draw_node(self, node_id, x, y):
        """Draw a node on the canvas"""
        # Draw circle
        self.canvas.create_oval(x-10, y-10, x+10, y+10, 
                              fill="yellow", outline="black", width=2,
                              tags=f"node_{node_id}")
        # Draw label
        self.canvas.create_text(x, y, text=node_id, font=("Arial", 9, "bold"),
                              tags=f"node_{node_id}")
        # Draw coordinates (small text)
        coord_text = f"({int(x)},{int(y)})"
        if self.real_scale_set:
            real_x, real_y = self.pixel_to_real(x, y)
            coord_text += f"\n({real_x:.1f},{real_y:.1f}m)"
        
        self.canvas.create_text(x, y-20, text=coord_text, 
                              font=("Arial", 7), fill="gray",
                              tags=f"node_{node_id}")
    
    def draw_edge(self, node1, node2, weight):
        """Draw an edge between two nodes"""
        x1, y1 = self.nodes[node1]["x"], self.nodes[node1]["y"]
        x2, y2 = self.nodes[node2]["x"], self.nodes[node2]["y"]
        
        # Draw line with curved appearance for realism
        self.canvas.create_line(x1, y1, x2, y2, width=3, fill="blue",
                              tags=f"edge_{node1}_{node2}")
        
        # Draw weight label
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        self.canvas.create_text(mid_x, mid_y, text=f"{weight:.1f}min", 
                              fill="red", font=("Arial", 8, "bold"),
                              tags=f"edge_{node1}_{node2}")
    
    def highlight_node(self, node_id, color):
        """Highlight a node with the specified color"""
        x, y = self.nodes[node_id]["x"], self.nodes[node_id]["y"]
        self.canvas.create_oval(x-12, y-12, x+12, y+12, 
                              outline=color, width=3, tags="highlight")
    
    def clear_selection(self):
        """Clear node selection"""
        self.canvas.delete("highlight")
        self.selected_nodes = []
        self.status_var.set("Edge mode: Click two nodes to connect them")
    
    def auto_detect_roads(self):
        """Attempt to automatically detect roads/paths in the image"""
        if not self.original_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        try:
            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(self.original_image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find lines using Hough transform
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                   minLineLength=50, maxLineGap=10)
            
            if lines is not None:
                # Draw detected lines
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    self.canvas.create_line(x1, y1, x2, y2, fill="green", width=2, tags="detected")
                
                self.status_var.set(f"Detected {len(lines)} potential road segments")
                messagebox.showinfo("Detection Complete", 
                                  f"Found {len(lines)} potential road segments (shown in green)")
            else:
                messagebox.showinfo("No Roads Found", "Could not detect any road segments")
                
        except Exception as e:
            messagebox.showerror("Error", f"Road detection failed: {str(e)}")
    
    def clear_all(self):
        """Clear all nodes and edges"""
        if messagebox.askyesno("Confirm", "Clear all nodes and edges?"):
            self.nodes = {}
            self.edges = {}
            self.selected_nodes = []
            self.canvas.delete("node")
            self.canvas.delete("edge")
            self.canvas.delete("highlight")
            self.canvas.delete("detected")
            self.status_var.set("Cleared all nodes and edges")
    
    def save_map(self):
        """Save the current map to a file"""
        if not self.nodes:
            messagebox.showwarning("Warning", "No nodes to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Map",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                map_data = {
                    "image_path": self.image_path,
                    "nodes": self.nodes,
                    "edges": self.edges,
                    "scale": {
                        "pixels_per_meter": self.pixels_per_meter,
                        "scale_set": self.real_scale_set
                    }
                }
                
                with open(file_path, 'w') as f:
                    json.dump(map_data, f, indent=2)
                
                self.status_var.set(f"Map saved to {os.path.basename(file_path)}")
                messagebox.showinfo("Success", "Map saved successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not save map: {str(e)}")
    
    def load_map(self):
        """Load a map from a file"""
        file_path = filedialog.askopenfilename(
            title="Load Map",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    map_data = json.load(f)
                
                # Load image if available
                if map_data.get("image_path") and os.path.exists(map_data["image_path"]):
                    self.image_path = map_data["image_path"]
                    self.original_image = Image.open(self.image_path)
                    max_size = (1200, 800)
                    self.original_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    self.display_image = self.original_image.copy()
                    self.photo = ImageTk.PhotoImage(self.display_image)
                    
                    self.canvas.delete("all")
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo, tags="background")
                
                # Load nodes and edges
                self.nodes = map_data.get("nodes", {})
                self.edges = map_data.get("edges", {})
                
                # Load scale
                scale_data = map_data.get("scale", {})
                self.pixels_per_meter = scale_data.get("pixels_per_meter", 1.0)
                self.real_scale_set = scale_data.get("scale_set", False)
                
                if self.real_scale_set:
                    self.scale_label.config(text=f"{self.pixels_per_meter:.2f} px/m", foreground="green")
                
                # Redraw everything
                self.redraw_map()
                
                self.status_var.set(f"Loaded map: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", "Map loaded successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not load map: {str(e)}")
    
    def redraw_map(self):
        """Redraw all nodes and edges"""
        # Clear existing drawings (except background)
        self.canvas.delete("node")
        self.canvas.delete("edge")
        
        # Draw all edges first
        for node1, connections in self.edges.items():
            for node2, weight in connections.items():
                if node1 < node2:  # Draw each edge only once
                    self.draw_edge(node1, node2, weight)
        
        # Draw all nodes
        for node_id, data in self.nodes.items():
            self.draw_node(node_id, data["x"], data["y"])
    
    def export_to_main(self):
        """Export the current map to the main GUI"""
        if not self.parent_gui or not self.nodes:
            messagebox.showwarning("Warning", "No nodes to export or no main GUI available")
            return
        
        try:
            # Clear existing graph in main GUI - FIX HERE
            self.parent_gui.graph = Graph()  # Use imported Graph class directly
            
            # Add nodes to main GUI
            for node_id, data in self.nodes.items():
                self.parent_gui.graph.add_node(node_id, {"x": data["x"], "y": data["y"]})
            
            # Add edges to main GUI
            for node1, connections in self.edges.items():
                for node2, weight in connections.items():
                    if node1 < node2:  # Add each edge only once
                        self.parent_gui.graph.add_edge(node1, node2, weight)
            
            # Update routing and refresh displays - FIX HERE TOO
            self.parent_gui.routing = Routing(self.parent_gui.graph)  # Use imported Routing class
            
            self.parent_gui.update_location_combos()
            self.parent_gui.draw_graph()
            
            messagebox.showinfo("Success", f"Exported {len(self.nodes)} nodes and {len(self.edges)} edges to main application")
            self.parent_gui.log_update(f"Imported map with {len(self.nodes)} intersections from image")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not export to main GUI: {str(e)}")
    
    def on_right_click(self, event):
        """Handle right-click context menu"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Find if we clicked on a node
        clicked_node = self.find_closest_node(x, y, max_distance=15)
        
        if clicked_node:
            # Create context menu for node
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label=f"Delete {clicked_node}", 
                                   command=lambda: self.delete_node(clicked_node))
            context_menu.add_command(label=f"Edit {clicked_node}", 
                                   command=lambda: self.edit_node(clicked_node))
            context_menu.tk_popup(event.x_root, event.y_root)
    
    def delete_node(self, node_id):
        """Delete a node and all its connections"""
        if messagebox.askyesno("Confirm Delete", f"Delete node {node_id} and all its connections?"):
            # Remove from nodes
            del self.nodes[node_id]
            
            # Remove all edges connected to this node
            if node_id in self.edges:
                connected_nodes = list(self.edges[node_id].keys())
                for connected in connected_nodes:
                    del self.edges[connected][node_id]
                del self.edges[node_id]
            
            # Remove from other nodes' edge lists
            for other_node in self.edges:
                if node_id in self.edges[other_node]:
                    del self.edges[other_node][node_id]
            
            # Redraw
            self.redraw_map()
            self.status_var.set(f"Deleted node {node_id}")
    
    def edit_node(self, node_id):
        """Edit a node's properties"""
        new_id = simpledialog.askstring("Edit Node", f"Enter new ID for {node_id}:", initialvalue=node_id)
        if new_id and new_id != node_id and new_id not in self.nodes:
            # Update node data
            self.nodes[new_id] = self.nodes[node_id]
            del self.nodes[node_id]
            
            # Update edges
            if node_id in self.edges:
                self.edges[new_id] = self.edges[node_id]
                del self.edges[node_id]
            
            # Update references in other edges
            for other_node in self.edges:
                if node_id in self.edges[other_node]:
                    self.edges[other_node][new_id] = self.edges[other_node][node_id]
                    del self.edges[other_node][node_id]
            
            self.redraw_map()
            self.status_var.set(f"Renamed {node_id} to {new_id}")
    
    def on_mouse_motion(self, event):
        """Update status with mouse coordinates"""
        if self.original_image:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            coord_text = f"Mouse: ({int(x)}, {int(y)})"
            
            if self.real_scale_set:
                real_x, real_y = self.pixel_to_real(x, y)
                coord_text += f" | Real: ({real_x:.1f}, {real_y:.1f})m"
            
            # Don't update status if we're in a specific mode with instructions
            if "mode:" not in self.status_var.get():
                self.status_var.set(coord_text)


def create_image_map(parent_gui=None):
    """Standalone function to create image map creator"""
    app = ImageMapCreator(parent_gui)
    if not parent_gui:  # If running standalone
        app.root.mainloop()
    return app
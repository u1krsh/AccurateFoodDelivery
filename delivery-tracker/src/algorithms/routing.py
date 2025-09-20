from collections import deque
import heapq

class Routing:
    def __init__(self, graph):
        self.graph = graph

    def find_shortest_path_bfs(self, start_node, end_node):
        """BFS implementation for finding shortest path"""
        if start_node not in self.graph.nodes or end_node not in self.graph.nodes:
            return None
        
        queue = deque([(start_node, [start_node])])
        visited = {start_node}
        
        while queue:
            current, path = queue.popleft()
            
            if current == end_node:
                return path
            
            for neighbor in self.graph.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None

    def find_shortest_path_dfs(self, start_node, end_node):
        """DFS implementation for finding path"""
        if start_node not in self.graph.nodes or end_node not in self.graph.nodes:
            return None
        
        def dfs_recursive(current, path, visited):
            if current == end_node:
                return path
            
            visited.add(current)
            
            for neighbor in self.graph.get_neighbors(current):
                if neighbor not in visited:
                    result = dfs_recursive(neighbor, path + [neighbor], visited.copy())
                    if result:
                        return result
            
            return None
        
        return dfs_recursive(start_node, [start_node], set())

    def shortest_path(self, start, end):
        """Dijkstra's algorithm for shortest path with weights"""
        if start not in self.graph.nodes or end not in self.graph.nodes:
            return None
        
        # Dijkstra's algorithm
        distances = {node: float('inf') for node in self.graph.nodes}
        distances[start] = 0
        previous = {}
        pq = [(0, start)]
        
        while pq:
            current_distance, current = heapq.heappop(pq)
            
            if current == end:
                # Reconstruct path
                path = []
                while current in previous:
                    path.append(current)
                    current = previous[current]
                path.append(start)
                return path[::-1]
            
            if current_distance > distances[current]:
                continue
            
            for neighbor in self.graph.get_neighbors(current):
                weight = self.graph.get_edge_weight(current, neighbor)
                distance = current_distance + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))
        
        return None

    def calculate_route_time(self, path):
        """Calculate total time for a given path"""
        if not path or len(path) < 2:
            return 0
        
        total_time = 0
        for i in range(len(path) - 1):
            total_time += self.graph.get_edge_weight(path[i], path[i + 1])
        return total_time
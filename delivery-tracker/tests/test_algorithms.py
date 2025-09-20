import unittest
from src.algorithms.bfs import bfs
from src.algorithms.dfs import dfs
from src.models.graph import Graph

class TestAlgorithms(unittest.TestCase):

    def setUp(self):
        self.graph = Graph()
        self.graph.add_edge('A', 'B', 1)
        self.graph.add_edge('A', 'C', 2)
        self.graph.add_edge('B', 'D', 1)
        self.graph.add_edge('C', 'D', 2)
        self.graph.add_edge('D', 'E', 1)

    def test_bfs(self):
        expected_path = ['A', 'B', 'D', 'E']
        path = bfs(self.graph, 'A', 'E')
        self.assertEqual(path, expected_path)

    def test_dfs(self):
        expected_path = ['A', 'C', 'D', 'E']
        path = dfs(self.graph, 'A', 'E')
        self.assertEqual(path, expected_path)

if __name__ == '__main__':
    unittest.main()
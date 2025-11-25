import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.assignment_service import AssignmentService
from models.driver import Driver
from models.delivery import Delivery
from models.graph import Graph

class TestAssignmentService(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        self.graph.add_node("A", {"x": 0, "y": 0})
        self.graph.add_node("B", {"x": 100, "y": 0})
        self.assignment_service = AssignmentService(self.graph)
        
        self.driver1 = Driver("D1", "Driver 1", "A")
        self.driver2 = Driver("D2", "Driver 2", "B")
        self.delivery = Delivery("DEL1", "A") # Delivery at A

    def test_score_driver(self):
        """Test driver scoring logic"""
        # Driver 1 is at A, delivery is at A. Distance = 0.
        score1 = self.assignment_service.score_driver(self.driver1, "A")
        
        # Driver 2 is at B, delivery is at A. Distance = 100.
        score2 = self.assignment_service.score_driver(self.driver2, "A")
        
        # Driver 1 should have higher score (closer)
        self.assertGreater(score1, score2)

    def test_find_best_driver(self):
        """Test finding the best driver"""
        drivers = {"D1": self.driver1, "D2": self.driver2}
        best_driver = self.assignment_service.find_best_driver(self.delivery, drivers)
        self.assertEqual(best_driver.driver_id, "D1")

if __name__ == '__main__':
    unittest.main()

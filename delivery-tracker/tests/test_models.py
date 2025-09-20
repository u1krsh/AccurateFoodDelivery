import unittest
from src.models.graph import Graph
from src.models.driver import Driver
from src.models.delivery import Delivery

class TestGraph(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        self.graph.add_node("A")
        self.graph.add_node("B")
        self.graph.add_edge("A", "B", 5)

    def test_add_node(self):
        self.graph.add_node("C")
        self.assertIn("C", self.graph.nodes)

    def test_add_edge(self):
        self.graph.add_edge("A", "C", 10)
        self.assertIn(("A", "C"), self.graph.edges)

    def test_edge_weight(self):
        weight = self.graph.get_edge_weight("A", "B")
        self.assertEqual(weight, 5)

class TestDriver(unittest.TestCase):
    def setUp(self):
        self.driver = Driver(driver_id="D1", current_location="A")

    def test_driver_initialization(self):
        self.assertEqual(self.driver.driver_id, "D1")
        self.assertEqual(self.driver.current_location, "A")

    def test_update_location(self):
        self.driver.update_location("B")
        self.assertEqual(self.driver.current_location, "B")

class TestDelivery(unittest.TestCase):
    def setUp(self):
        self.delivery = Delivery(delivery_id="DEL1", destination="B")

    def test_delivery_initialization(self):
        self.assertEqual(self.delivery.delivery_id, "DEL1")
        self.assertEqual(self.delivery.destination, "B")

    def test_update_progress(self):
        self.delivery.update_progress("In Transit")
        self.assertEqual(self.delivery.status, "In Transit")

if __name__ == '__main__':
    unittest.main()
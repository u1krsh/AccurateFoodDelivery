import unittest
import sys
import os
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ml.time_predictor import TimePredictor
from ml.demand_predictor import DemandPredictor

class TestMLComponents(unittest.TestCase):
    def setUp(self):
        self.time_predictor = TimePredictor()
        self.demand_predictor = DemandPredictor()

    def test_time_predictor_training(self):
        """Test that the time predictor can train without errors"""
        # Create a dummy csv if needed or rely on existing
        # For test stability, let's mock the data loading or ensure file exists
        # But here we just test the train method
        result = self.time_predictor.train()
        self.assertTrue(result or not os.path.exists(self.time_predictor.data_path))
        
    def test_time_predictor_prediction(self):
        """Test prediction output"""
        self.time_predictor.train()
        prediction = self.time_predictor.predict("Italian", 15, 5.0)
        self.assertIsInstance(prediction, float)
        self.assertGreater(prediction, 0)

    def test_demand_predictor(self):
        """Test demand hotspot prediction"""
        nodes = {
            "A": {"x": 100, "y": 100},
            "B": {"x": 200, "y": 200},
            "C": {"x": 300, "y": 300}
        }
        self.demand_predictor.generate_synthetic_history(nodes)
        hotspots = self.demand_predictor.predict_hotspots()
        self.assertTrue(len(hotspots) <= 3)
        if len(hotspots) > 0:
            self.assertEqual(len(hotspots[0]), 2) # x, y coordinates

if __name__ == '__main__':
    unittest.main()

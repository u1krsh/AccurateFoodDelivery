import sys
import os
import unittest

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ml.time_predictor import TimePredictor

class TestEnhancedML(unittest.TestCase):
    def test_enhanced_training_and_prediction(self):
        print("\nTesting Enhanced TimePredictor...")
        predictor = TimePredictor()
        
        # Train
        success = predictor.train()
        self.assertTrue(success, "Model training failed")
        
        # Predict with new features
        # Cuisine, PrepTime, Distance, Traffic, Weather, TimeOfDay, DriverRating
        pred_time = predictor.predict(
            cuisine="Italian",
            base_prep_time=20,
            distance=5.0,
            traffic_level="High",
            weather="Rain",
            time_of_day="Dinner",
            driver_rating=4.5
        )
        
        print(f"Predicted time (Italian, 5km, High Traffic, Rain): {pred_time:.2f} mins")
        self.assertGreater(pred_time, 20, "Prediction should be greater than prep time")
        
        # Predict with another scenario (Clear, Low Traffic)
        pred_time_fast = predictor.predict(
            cuisine="Italian",
            base_prep_time=20,
            distance=5.0,
            traffic_level="Low",
            weather="Clear",
            time_of_day="Afternoon",
            driver_rating=4.5
        )
        print(f"Predicted time (Italian, 5km, Low Traffic, Clear): {pred_time_fast:.2f} mins")
        
        self.assertLess(pred_time_fast, pred_time, "Clear/Low traffic should be faster than Rain/High traffic")

if __name__ == '__main__':
    unittest.main()

import unittest
from src.services.tracking_service import TrackingService
from src.models.driver import Driver
from src.models.delivery import Delivery

class TestTrackingService(unittest.TestCase):

    def setUp(self):
        self.tracking_service = TrackingService()
        self.driver = Driver(driver_id="D1", current_location=(0, 0))
        self.delivery = Delivery(delivery_id="DL1", destination=(5, 5))

    def test_add_driver(self):
        self.tracking_service.add_driver(self.driver)
        self.assertIn(self.driver.driver_id, self.tracking_service.drivers)

    def test_update_driver_location(self):
        self.tracking_service.add_driver(self.driver)
        new_location = (1, 1)
        self.tracking_service.update_driver_location(self.driver.driver_id, new_location)
        self.assertEqual(self.tracking_service.drivers[self.driver.driver_id].current_location, new_location)

    def test_track_delivery(self):
        self.tracking_service.add_driver(self.driver)
        self.tracking_service.track_delivery(self.driver.driver_id, self.delivery)
        self.assertEqual(self.tracking_service.drivers[self.driver.driver_id].current_delivery, self.delivery)

    def test_complete_delivery(self):
        self.tracking_service.add_driver(self.driver)
        self.tracking_service.track_delivery(self.driver.driver_id, self.delivery)
        self.tracking_service.complete_delivery(self.driver.driver_id)
        self.assertIsNone(self.tracking_service.drivers[self.driver.driver_id].current_delivery)

if __name__ == '__main__':
    unittest.main()
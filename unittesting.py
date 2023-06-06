import unittest
from main import ParkingApp


class TestParkingApp(unittest.TestCase):
    def setUp(self):
        self.app = ParkingApp()

    def test_distinct_zone_numbers(self):
        self.assertEqual(self.app.distinct_zone_numbers(), 10)
        self.assertNotEqual(self.app.distinct_zone_numbers(), 18)
        self.assertNotEqual(self.app.distinct_zone_numbers(), 4)
        self.assertNotEqual(self.app.distinct_zone_numbers(), -2)


class TestValidationMethods(unittest.TestCase):

    def setUp(self):
        self.app = ParkingApp()

    def test_validate_password_valid(self):
        password = "StrongPassword123"
        res = self.app.validate_password(password)
        self.assertTrue(res, f"Expected {password} to be a valid password")

    def test_validate_password_invalid(self):
        password = "weak"
        res = self.app.validate_password(password)
        self.assertFalse(res, f"Expected {password} to be an invalid password")


# loader = unittest.TestLoader()
# suite = loader.loadTestsFromTestCase(TestParkingApp)

loader = unittest.TestLoader()
suite = loader.loadTestsFromTestCase(TestValidationMethods)

runner = unittest.TextTestRunner()
result = runner.run(suite)

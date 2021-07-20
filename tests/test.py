import unittest

from src.step_model import Model

class TestCase(unittest.TestCase):
    def test_parsing(self):
        Model("test")
        self.assertEqual(True, False)

    def test_faces(self):
        pass

if __name__ == '__main__':
    unittest.main()

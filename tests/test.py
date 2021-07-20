import unittest

from src.step_model import Model

class TestCase(unittest.TestCase):
    def test_parsing(self):
        model = Model("testfiles/zylinder.step")
        print(model)


    def test_faces(self):
        pass

if __name__ == '__main__':
    unittest.main()

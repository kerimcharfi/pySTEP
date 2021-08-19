import unittest
import trimesh.viewer

from src.step_model import Model

class TestCase(unittest.TestCase):
    def test_parsing(self):
        model = Model("testfiles/zylinder.step")
        model = Model("testfiles/wires.step")
        print(model)

    def test_faces(self):
        scene = trimesh.scene.Scene()
        model = Model("testfiles/draht.step")
        for edge in model.solids[0].edges:
            path = trimesh.load_path(edge.discretized)
            scene.add_geometry(path)
        trimesh.viewer.SceneViewer(scene)

    def test_intersection(self):
        pass


if __name__ == '__main__':
    unittest.main()

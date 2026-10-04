import unittest
import experiment

class ExperimentTests(unittest.TestCase):
    def test_decision_and_variance_reduction(self):
        result = experiment.analyze(experiment.make_demo_experiment(n=6000))
        self.assertIn(result["decision"], {"LAUNCH", "DO NOT LAUNCH"})
        self.assertGreater(result["cuped_variance_reduction"], 0)

if __name__ == "__main__":
    unittest.main()

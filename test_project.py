import unittest
import experiment

class ExperimentTests(unittest.TestCase):
    def test_decision_and_variance_reduction(self):
        result = experiment.analyze(experiment.make_demo_experiment(n=6000))
        self.assertIn(result["decision"], {"LAUNCH", "DO NOT LAUNCH"})
        self.assertGreater(result["cuped_variance_reduction"], 0)

    def test_diagnostics_and_guardrails(self):
        data = experiment.make_demo_experiment(n=6000)
        diagnostics = experiment.experiment_diagnostics(data)
        result = experiment.analyze(data)
        self.assertGreater(diagnostics["srm_p_value"], 0.01)
        self.assertLess(abs(diagnostics["pre_spend_standardized_difference"]), 0.1)
        self.assertIn("refund_rate_difference", result["guardrails"])

if __name__ == "__main__":
    unittest.main()

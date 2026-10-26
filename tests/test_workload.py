import tempfile
import unittest
from pathlib import Path

from workload.aggregate_risk import percentile, summarize
from workload.simulate_rate_risk import simulate


class SimulationTests(unittest.TestCase):
    def test_same_seed_reproduces_losses(self) -> None:
        first = simulate(20, 11, 1_000_000, 4.2, 25)
        second = simulate(20, 11, 1_000_000, 4.2, 25)
        self.assertEqual(first["losses_usd"], second["losses_usd"])

    def test_rejects_non_positive_sample_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "samples"):
            simulate(0, 11, 1_000_000, 4.2, 25)

    def test_rejects_non_finite_model_parameters(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            simulate(1, 11, float("nan"), 4.2, 25)


class AggregationTests(unittest.TestCase):
    def test_percentile_uses_linear_interpolation(self) -> None:
        self.assertEqual(percentile([10, 20, 30, 40], 0.95), 38.5)

    def test_aggregates_task_results_before_calculating_var(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_paths = []
            for task_id, task_losses in enumerate(([1.0, 2.0], [3.0, 4.0])):
                result_path = Path(temp_dir) / f"task-{task_id}.json"
                result_path.write_text(
                    '{"samples":2,"elapsed_seconds":0.5,"losses_usd":'
                    f"{list(task_losses)}"
                    "}",
                    encoding="utf-8",
                )
                result_paths.append(result_path)

            summary = summarize(result_paths)

        self.assertEqual(summary["tasks"], 2)
        self.assertEqual(summary["samples"], 4)
        self.assertAlmostEqual(summary["var_95_usd"], 3.85)
        self.assertEqual(summary["sum_worker_seconds"], 1.0)


if __name__ == "__main__":
    unittest.main()

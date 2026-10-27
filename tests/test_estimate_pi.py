import unittest

from workload.estimate_pi import estimate_pi


class EstimatePiTests(unittest.TestCase):
    def test_same_seed_returns_same_result(self) -> None:
        self.assertEqual(estimate_pi(1000, 42), estimate_pi(1000, 42))

    def test_estimate_is_close_to_pi_for_large_sample(self) -> None:
        _, estimate = estimate_pi(100_000, 42)
        self.assertAlmostEqual(estimate, 3.14, delta=0.03)

    def test_rejects_zero_points(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 1"):
            estimate_pi(0, 42)


if __name__ == "__main__":
    unittest.main()

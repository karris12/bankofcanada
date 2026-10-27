#!/usr/bin/env python3
"""Estimate pi with a small Monte Carlo simulation."""

import argparse
import random
import time


def estimate_pi(points: int, seed: int) -> tuple[int, float]:
    if points < 1:
        raise ValueError("points must be at least 1")

    generator = random.Random(seed)
    inside_circle = sum(
        generator.random() ** 2 + generator.random() ** 2 <= 1
        for _ in range(points)
    )
    return inside_circle, 4 * inside_circle / points


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=int, default=5_000_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.points < 1:
        parser.error("--points must be at least 1")

    started = time.perf_counter()
    inside_circle, pi_estimate = estimate_pi(args.points, args.seed)
    elapsed = time.perf_counter() - started

    print(f"Points: {args.points}")
    print(f"Points inside circle: {inside_circle}")
    print(f"Estimated pi: {pi_estimate:.6f}")
    print(f"Elapsed seconds: {elapsed:.2f}")


if __name__ == "__main__":
    main()

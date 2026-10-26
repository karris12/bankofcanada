#!/usr/bin/env python3
"""Generate a deterministic synthetic portfolio rate-shock loss sample."""

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Any


def simulate(
    samples: int,
    seed: int,
    notional_usd: float,
    duration_years: float,
    shock_sigma_bps: float,
) -> dict[str, Any]:
    if samples < 1:
        raise ValueError("samples must be at least 1")
    parameters = (notional_usd, duration_years, shock_sigma_bps)
    if any(not math.isfinite(value) or value <= 0 for value in parameters):
        raise ValueError("notional, duration, and shock sigma must be finite and positive")

    rng = random.Random(seed)
    started = time.perf_counter()
    losses = [
        notional_usd * duration_years * rng.gauss(0, shock_sigma_bps) / 10_000
        for _ in range(samples)
    ]
    elapsed = time.perf_counter() - started
    return {
        "seed": seed,
        "samples": samples,
        "notional_usd": notional_usd,
        "duration_years": duration_years,
        "shock_sigma_bps": shock_sigma_bps,
        "elapsed_seconds": elapsed,
        "losses_usd": losses,
    }


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than 0")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=positive_int, default=100_000)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--notional-usd", type=positive_float, default=1_000_000_000)
    parser.add_argument("--duration-years", type=positive_float, default=4.2)
    parser.add_argument("--shock-sigma-bps", type=positive_float, default=25.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = simulate(
        args.samples,
        args.seed,
        args.notional_usd,
        args.duration_years,
        args.shock_sigma_bps,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output_file:
        json.dump(result, output_file, separators=(",", ":"))
        output_file.write("\n")
    print(
        f"seed={args.seed} samples={args.samples} "
        f"elapsed_seconds={result['elapsed_seconds']:.3f} output={args.output}"
    )


if __name__ == "__main__":
    main()

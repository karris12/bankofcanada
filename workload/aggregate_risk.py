#!/usr/bin/env python3
"""Combine task results and calculate synthetic portfolio loss statistics."""

import argparse
import json
import math
from pathlib import Path
from typing import Any, Union


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("at least one loss is required")
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1")

    ordered = sorted(values)
    rank = probability * (len(ordered) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    fraction = rank - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def load_losses(paths: list[Path]) -> tuple[list[float], float]:
    losses: list[float] = []
    worker_seconds = 0.0
    for path in paths:
        with path.open(encoding="utf-8") as input_file:
            result: dict[str, Any] = json.load(input_file)
        task_losses = result.get("losses_usd")
        if not isinstance(task_losses, list) or not task_losses:
            raise ValueError(f"{path} has no losses_usd results")
        if result.get("samples") != len(task_losses):
            raise ValueError(f"{path} sample count does not match its losses")
        if not all(isinstance(loss, (int, float)) and math.isfinite(loss) for loss in task_losses):
            raise ValueError(f"{path} contains a non-finite or non-numeric loss")
        elapsed = result.get("elapsed_seconds")
        if not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError(f"{path} has an invalid elapsed_seconds value")
        losses.extend(task_losses)
        worker_seconds += elapsed
    return losses, worker_seconds


def summarize(paths: list[Path]) -> dict[str, Union[float, int]]:
    losses, worker_seconds = load_losses(paths)
    var_95 = percentile(losses, 0.95)
    tail_losses = [loss for loss in losses if loss >= var_95]
    return {
        "tasks": len(paths),
        "samples": len(losses),
        "mean_loss_usd": sum(losses) / len(losses),
        "var_95_usd": var_95,
        "expected_shortfall_95_usd": sum(tail_losses) / len(tail_losses),
        "sum_worker_seconds": worker_seconds,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_files", nargs="+", type=Path)
    args = parser.parse_args()

    summary = summarize(args.result_files)
    print(f"Completed tasks: {summary['tasks']}")
    print(f"Monte Carlo samples: {summary['samples']}")
    print(f"Mean loss: ${summary['mean_loss_usd']:,.2f}")
    print(f"95th percentile loss (VaR proxy): ${summary['var_95_usd']:,.2f}")
    print(f"Mean loss in 95th percentile tail: ${summary['expected_shortfall_95_usd']:,.2f}")
    print(f"Sum of worker compute seconds: {summary['sum_worker_seconds']:.3f}")


if __name__ == "__main__":
    main()

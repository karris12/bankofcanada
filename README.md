# Bank of Canada interview demo: Azure CycleCloud + Slurm

A small, reproducible HPC demonstration for a Cloud HPC Architect interview. It runs an embarrassingly parallel Monte Carlo simulation of a **synthetic** interest-rate portfolio loss model using a Slurm job array. Azure CycleCloud provisions the Slurm environment and scales a tightly capped set of compute nodes on demand.

> This is an educational workload, not a Bank of Canada model, market forecast, or financial advice. It uses no real or confidential data.

## What the demo shows

- HPC concepts: independent simulations, deterministic random seeds, job arrays, shared output, aggregation, and reproducibility.
- Slurm operations: submit, inspect, and account for work with `sbatch`, `squeue`, `sinfo`, and `sacct`.
- Cloud HPC architecture: CycleCloud as the orchestration layer, Slurm as the scheduler, and separate scheduler and elastic compute capacity.
- Cost awareness: small workload, bounded compute capacity, autoscaling, and explicit teardown.

## Repository map

- [`workload/`](workload/) - simulation, aggregation, and Slurm job-array script.
- [`tests/`](tests/) - standard-library tests; no Python packages to install.
- [`docs/DEMO_RUNBOOK.md`](docs/DEMO_RUNBOOK.md) - beginner-friendly PowerShell/local steps, Azure portal provisioning, secure login, Linux commands with example output, troubleshooting, and cleanup.

## Validate locally first

Requires Python 3.9 or later:

```bash
python -m unittest discover -s tests -v
python workload/simulate_rate_risk.py --samples 1000 --seed 7 --output results/local-0.json
python workload/aggregate_risk.py results/local-0.json
```

For a four-task local simulation:

```bash
mkdir -p results
for task in 0 1 2 3; do
  python workload/simulate_rate_risk.py \
    --samples 100000 \
    --seed "$((20261025 + task))" \
    --output "results/local-${task}.json"
done
python workload/aggregate_risk.py results/local-*.json
```

In Windows PowerShell, create `results` with `New-Item -ItemType Directory -Force results` instead of `mkdir -p`.
To run all four local tasks from PowerShell:

```powershell
New-Item -ItemType Directory -Force results | Out-Null
for ($task = 0; $task -lt 4; $task++) {
  python workload/simulate_rate_risk.py `
    --samples 100000 `
    --seed (20261025 + $task) `
    --output "results/local-$task.json"
}
$resultFiles = Get-ChildItem results\local-*.json | ForEach-Object { $_.FullName }
python workload/aggregate_risk.py @resultFiles
```

The same task program runs in the Slurm array. The serial local run is a functional baseline, not a meaningful performance comparison against a distributed cluster.

## Azure demo in one sentence

Deploy a small Azure CycleCloud Workspace for Slurm (or an existing CycleCloud Slurm 4 environment), cap the execute partition at **two small CPU nodes**, submit the four-task array, inspect job and node states, aggregate the results, record elapsed time and cost, then delete the demo resources.

**Start with the [beginner's walkthrough](docs/DEMO_RUNBOOK.md), not with Azure commands.** It separates deploying the CycleCloud workspace from creating the Slurm cluster and shows the exact order to proceed.

**Do not assume the Azure Free Account makes this deployment free or that `$180` will cover a particular runtime.** VM availability, regional prices, disks, networking, secure login, Marketplace terms, quotas, and remaining-credit expiry all matter. Check the [cost and setup checklist](docs/DEMO_RUNBOOK.md#important-should-you-deploy-to-azure) before provisioning anything. This repository does not deploy Azure resources automatically.

## Official references

- [Azure CycleCloud overview](https://learn.microsoft.com/azure/cyclecloud/overview?view=cyclecloud-8)
- [Azure CycleCloud Workspace for Slurm overview](https://learn.microsoft.com/azure/cyclecloud/overview-ccws?view=cyclecloud-8)
- [Plan a CycleCloud Workspace for Slurm deployment](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8)
- [Configure and manage CycleCloud Slurm 4 clusters](https://learn.microsoft.com/azure/cyclecloud/slurm-4?view=cyclecloud-8)
- [Operate and troubleshoot CycleCloud Slurm 4 clusters](https://learn.microsoft.com/azure/cyclecloud/slurm-4-operations?view=cyclecloud-8)
- [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator/)

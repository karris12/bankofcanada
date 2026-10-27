# Tiny Slurm demo

This repository is a small, beginner-friendly way to practice submitting and checking one Slurm job on Azure CycleCloud.

The job estimates pi by randomly placing points inside a square and counting how many land inside a circle. It uses one CPU on one HTC compute node. There are no job arrays, databases, financial assumptions, extra Python packages, or result-processing steps.

## Run locally first

Requires Python 3:

```powershell
python workload\estimate_pi.py --points 10000 --seed 42
```

Expected output looks like this (the estimate and run time may vary):

```text
Points: 10000
Points inside circle: 7815
Estimated pi: 3.126000
Elapsed seconds: 0.01
```

## Run on your CycleCloud Slurm cluster

Read [`docs/DEMO_RUNBOOK.md`](docs/DEMO_RUNBOOK.md) for the short Azure, quota, login, and Slurm walkthrough. Run these commands **on the Linux Slurm login node**, from this repository's directory:

```bash
sbatch workload/demo.sbatch
squeue -u "$USER"
sinfo --partition=htc
cat slurm-JOBID.out
```

Replace `JOBID` with the number printed by `sbatch`. The job normally finishes quickly, so `squeue` may already be empty; its output is saved in `slurm-JOBID.out`.

> The existing Azure deployment hit an East US regional-core quota limit. Resolve that quota issue before retrying cluster nodes or running Slurm jobs. Azure resources can continue to cost money while the cluster is unavailable.

#!/usr/bin/env bash
#SBATCH --job-name=pi-demo
#SBATCH --partition=htc
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:02:00
#SBATCH --output=slurm-%j.out

set -euo pipefail

echo "Slurm job ID: ${SLURM_JOB_ID}"
echo "Compute node: $(hostname)"
python3 "${SLURM_SUBMIT_DIR}/workload/estimate_pi.py" --points 5000000 --seed 42

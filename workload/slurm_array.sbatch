#!/usr/bin/env bash
#SBATCH --job-name=rate-risk
#SBATCH --array=0-3%2
#SBATCH --partition=hpc
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --output=%x-%A_%a.out

set -euo pipefail

TASK_ID="${SLURM_ARRAY_TASK_ID:?Submit this script as a Slurm array}"
JOB_ID="${SLURM_ARRAY_JOB_ID:?Missing Slurm array job ID}"
SAMPLES_PER_TASK="${SAMPLES_PER_TASK:-100000}"
SEED_BASE="${SEED_BASE:-20261025}"
OUTPUT_DIR="${SLURM_SUBMIT_DIR}/results"

mkdir -p "${OUTPUT_DIR}"
python3 "${SLURM_SUBMIT_DIR}/workload/simulate_rate_risk.py" \
  --samples "${SAMPLES_PER_TASK}" \
  --seed "$((SEED_BASE + TASK_ID))" \
  --output "${OUTPUT_DIR}/${JOB_ID}_${TASK_ID}.json"

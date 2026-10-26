# Interview demo runbook

## The story

Present this as a cloud-HPC proof of concept, not a claim about Bank of Canada production systems:

> "I built a small synthetic interest-rate risk simulation to show how independent Monte Carlo trials can be spread across Slurm array tasks. CycleCloud supplies and scales the compute capacity; Slurm schedules the work; every task writes a reproducible result, and a reducer calculates portfolio-level statistics. I kept the worker count bounded, used no real data, and included explicit cost and cleanup controls."

The first-order approximation is `loss ~= notional x duration x rate shock`. Each task draws deterministic rate shocks from a normal distribution using its own seed. The reducer combines all samples before calculating the 95th-percentile loss proxy and the mean of the tail. This is intentionally not a validated financial risk model.

## Local preflight

Run these from the repository root before touching Azure:

```bash
python -m unittest discover -s tests -v
python workload/simulate_rate_risk.py --samples 1000 --seed 7 --output results/local-0.json
python workload/aggregate_risk.py results/local-0.json
```

On Windows PowerShell, create the output directory with `New-Item -ItemType Directory -Force results` first if it does not exist. Python is standard-library only.

## Azure setup and cost guardrails

### Decide whether to deploy

CycleCloud and Slurm require billable Azure infrastructure; "Free Account" does not mean this HPC cluster is free. Before starting, check:

1. The Azure portal shows at least `$180` of **unexpired** credit for the subscription you will use. Check the credit end date and any Marketplace restrictions.
2. You can create resources in a **new, dedicated** resource group and have the subscription permissions the selected deployment requires. Do not deploy into a resource group containing unrelated resources.
3. The target region has quota and capacity for the selected CPU VM sizes.
4. Azure Pricing Calculator has an estimate for that region and the complete architecture. Include the CycleCloud VM, scheduler/sign-in nodes, up to two compute nodes, managed disks, IP/networking, and any Marketplace charges. Prices and quotas vary; this repository cannot promise that `$180` covers a particular deployment or duration.
5. You understand that a Cost Management budget is an alert, **not** a hard spending cap. Check actual accumulated cost in Cost Management while the demo is running.

Use the [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator/) and [CycleCloud Workspace deployment planning checklist](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8).

### Recommended guided route

For a first Azure Slurm cluster, Microsoft's **Azure CycleCloud Workspace for Slurm** Marketplace solution is the most guided route. It deploys CycleCloud and a predefined Slurm environment, but it is not a free or serverless service. Its greenfield deployment creates multiple resources and role assignments. Microsoft's current planning checklist requires subscription-level `Contributor` and `User Access Administrator` permissions and an Entra application registration; do not try to work around organization policy or grant yourself roles you do not have.

1. In [Azure portal](https://portal.azure.com), confirm the right directory and subscription, then create a dedicated resource group such as `rg-hpc-interview-demo`.
2. In Azure Marketplace, search for **Azure CycleCloud Workspace for Slurm**. Read the current offer, publisher, plan, terms, architecture, and estimated charges before selecting **Create**. If the offer, required permissions, terms, quota, or estimate are unclear, stop and ask your subscription administrator or continue with the local demo.
3. Follow Microsoft's [deployment planning checklist](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8). Select a greenfield deployment only in the dedicated resource group. Avoid optional Lustre/ANF filesystems, GPU nodes, high availability, Open OnDemand, and other add-ons for this interview-sized experiment unless you have priced and specifically need them.
4. In the Slurm cluster settings, use a small, non-GPU CPU VM available in your region and quota. Set an explicit upper bound of **two execute nodes** (and no more than four worker vCPUs total for this demo); verify the effective limit in the deployed configuration. Keep the autoscale idle timeout short. Template labels and defaults can change between releases, so verify the values in the version you deploy.
5. Keep compute nodes private. Use the deployment's supported sign-in path, Bastion, or a source-IP-restricted route. Never expose SSH to `0.0.0.0/0`, put passwords/private keys in Git, or upload real financial, personal, or Bank of Canada data.
6. Before starting the cluster, take a screenshot or note of the resource group, region, selected VM sizes, node cap, and current credit/budget. These are useful architecture evidence for the interview.

> This Marketplace route is more complete than a minimal one-VM tutorial and may not fit your credit or account permissions. Do not click through deployment defaults blindly. If the full estimate is not comfortably within your available credit, stop before creating resources; use the tested workload locally and present the architecture and deployment plan instead.

## Run the Slurm demo

Use the deployment's documented SSH/VS Code path to reach its sign-in node. The commands below are for that Linux environment. Put this repository in a shared directory mounted on compute nodes; the Slurm working directory and result directory must be visible to both the submit host and workers.

```bash
git clone https://github.com/karris12/bankofcanada.git
cd bankofcanada
python3 --version
srun --nodes=1 --ntasks=1 python3 --version
```

The first version check is on the sign-in node; the `srun` check verifies Python 3 on a compute node. If Python 3 is not present on compute nodes, stop and use the supported image customization or container path for the deployed CycleCloud/Slurm version; do not assume a package installed only on the sign-in node is available to workers.

Submit four reproducible tasks, with at most two running concurrently:

```bash
mkdir -p results
JOB_ID=$(sbatch --parsable workload/slurm_array.sbatch)
echo "Submitted array job ${JOB_ID}"
squeue --jobs "${JOB_ID}"
sinfo --Node --long
```

The script defaults to 100,000 samples per task. To increase useful compute time for observing autoscale, submit with a larger bounded sample count, for example:

```bash
SAMPLES_PER_TASK=500000 sbatch --parsable workload/slurm_array.sbatch
```

Capture the returned job ID when using the second command. Do not raise the node cap or run multiple copies to make the chart look busier. A small workload may finish before a newly provisioned node is visible; explain that startup latency and workload duration affect measured scale-out.

After the tasks finish, inspect completion and aggregate their output:

```bash
squeue --jobs "${JOB_ID}"
sinfo --Node --long
python3 workload/aggregate_risk.py results/"${JOB_ID}"_*.json
```

If Slurm job accounting is enabled in the environment, inspect wall time and allocation with:

```bash
sacct --jobs "${JOB_ID}" --format=JobID,JobName%18,State,Elapsed,AllocCPUS,NodeList,ExitCode
```

If accounting is not configured, show `squeue`/`sinfo` while the work is active, the Slurm stdout files, the task JSON outputs, and the aggregator output instead. Do not enable a separately billed database just to make `sacct` work for this short demo. Record end-to-end elapsed time separately from the simulation's worker seconds; do not claim a speedup unless you run a fair, repeated baseline and account for queue and VM startup time.

## What to show (about 5 minutes)

1. **Architecture (45 sec):** CycleCloud is the cluster lifecycle/autoscaling layer; Slurm is the scheduler; execute nodes are separate from the sign-in/scheduler roles; shared storage carries scripts and results.
2. **Workload (45 sec):** Show the synthetic model, task-specific deterministic seeds, array concurrency cap, and reducer. Explain why the independent trials are parallelizable.
3. **Live operations (2 min):** Submit the array, show its job ID and `squeue`, show nodes/partitions with `sinfo`, then show the task outputs and aggregated VaR proxy/tail mean.
4. **Architecture judgment (1 min):** Discuss startup overhead, shared-filesystem assumptions, worker sizing/quota, reproducibility, and why Slurm arrays fit independent trials. Mention that MPI tightly-coupled work would need a different job shape and network/VM sizing.
5. **Cost and risk (45 sec):** Point out the hard two-node cap, short run, synthetic data, private access, Cost Management checks, and teardown. Be candid that this is a demo model, not a production risk engine.

### Hiring-manager questions to prepare for

- **Why CycleCloud instead of Azure Batch?** CycleCloud fits when a team needs a familiar Slurm scheduler, scheduler policies, or HPC workflow portability. Batch may be simpler when the workload does not need scheduler ownership.
- **How would you productionize this?** Validate the financial model and input data, define service-level objectives, benchmark storage and network behavior, choose the right VM family, add identity and least-privilege controls, monitor queue and job outcomes, test node failures, set quota/cost policy, and document recovery and ownership.
- **How do you know scaling helped?** Compare repeated runs with the same samples, seeds, software, and VM configuration; separate queue/startup time from compute time; report throughput and cost per completed sample; include confidence intervals and recognize small-job overhead.
- **What can go wrong?** Quota/capacity denial, image or Python mismatch, unavailable shared paths, failed or preempted nodes, output collisions, non-reproducible seeds, and surprise storage/network/Marketplace costs. State the checks and recovery action for each.

## Tear down the same day

1. Save only the screenshots/metrics needed for the interview. Do not commit generated results, credentials, SSH keys, subscription IDs, or real data.
2. Stop or terminate the Slurm cluster using the deployed CycleCloud interface so execute nodes are removed or deallocated.
3. In the Azure portal, inspect the dedicated resource group and its resources, then delete that **dedicated demo resource group** when you are sure it contains no unrelated resources.
4. Check Cost Management and the resource list again for leftovers, such as disks, public IPs, databases, or Marketplace-created resources outside that resource group. Clean up only resources you positively identify as belonging to this demo.
5. Recheck usage/cost after deletion. Deleting a cluster alone might not delete separately provisioned dependencies; for example, CycleCloud Slurm job accounting can use a separate Azure Database for MySQL resource.

Keep the project repository even after deleting the Azure resources; the synthetic workload and local tests continue to work.

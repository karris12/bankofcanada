# Simple CycleCloud + Slurm demo

This version is deliberately small: one Python file, one Slurm job, one output file. The job estimates pi using random points. You will practice the core Slurm flow: **submit → check → read the output**.

## Important: your Azure quota error

Your latest error says East US has a **4-core limit, all 4 cores are in use**, and a failed VM needs **4 additional cores**. The requested VM cannot start until Azure approves more regional quota.

Before retrying:

1. In Azure portal, open **Quotas** for **Compute → East US**. Check **Total Regional vCPUs** and any VM-family quota shown in the failure.
2. Ask your Azure subscription administrator (or submit a quota-increase request) for enough quota to cover the existing 4-core CycleCloud VM, the Slurm scheduler/login VM or VMs, and **one small HTC worker**. The error's 8-core minimum covers only the currently failing 4-core VM in addition to today's usage; it might not leave cores for the demo worker. Check the actual VM sizes in CycleCloud before choosing a request.
3. Check Cost Management. A quota increase is not a VM; starting the nodes uses billable resources. If quota is denied or the estimate is uncomfortable, don't keep retrying. You can still practice the program locally.

The VM quota error must be fixed before Slurm commands can run on a worker. `sbatch` submits to a working Slurm scheduler; it does not create missing quota or repair a failed cluster node.

## What this demo does

The Python program throws random points into a square. A circle fits inside that square. It estimates pi by counting the points that land inside the circle:

```text
pi estimate = 4 x (points inside circle / all points)
```

More points usually give a closer estimate. This is a toy compute workload, not a financial model.

## 1. Test the program on Windows first

Open PowerShell in your local repository:

```powershell
Set-Location "$HOME\Documents\devopsProject\hpc"
python workload\estimate_pi.py --points 10000 --seed 42
```

Example output (your timings and count may differ):

```text
Points: 10000
Points inside circle: 7815
Estimated pi: 3.126000
Elapsed seconds: 0.01
```

## 2. Wait for the Slurm cluster to be healthy

Open CycleCloud in the browser. The cluster needs a healthy scheduler and a login node before you can submit a job. Resolve the quota failure above first; then use **Retry** on the failed node only if the quota is approved and the node configuration is still correct.

For this low-cost demo, configure **one maximum HTC worker node**, using the smallest suitable CPU VM permitted by quota. Do not start HPC or GPU nodes. HTC is suitable because the demo is a standalone task and doesn't need tightly coupled multi-node communication. If the CycleCloud form requires a minimum HPC value, leave it at its minimum and do not submit a job to that partition.

Wait until CycleCloud reports the required scheduler/login nodes as ready and no node is failed. The demo compute node can be created on demand when Slurm starts the job. Keep checking Cost Management; the CycleCloud VM and Bastion can incur costs even while Slurm is idle.

## 3. Connect to the Linux Slurm login node

Use the secure login-node access method configured in your Azure deployment. For the workspace you described, use Azure Bastion as in Microsoft's [login-node access guide](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-login-node-with-bastion?view=cyclecloud-8). Select the **login/authentication node** in CycleCloud and copy its VM resource ID; do not use the CycleCloud VM's resource ID for Slurm commands.

From Windows PowerShell, sign in and set your subscription:

```powershell
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

Then connect using the Bastion name, resource group, login-node resource ID, and SSH private key from your deployment:

```powershell
az network bastion ssh `
  --name "bastion" `
  --resource-group "rg-hpc-interview-demo" `
  --target-resource-id "PASTE_LOGIN_NODE_RESOURCE_ID" `
  --auth-type ssh-key `
  --username "hpcadmin" `
  --ssh-key "$HOME\.ssh\hpc-interview-demo"
```

Replace the resource ID with the actual login/authentication VM resource ID. If your deployment uses a different username or key path, use that value. Keep the private key on your computer; never paste it into chat or commit it to GitHub.

After connecting, the prompt is a **Linux shell on the login node**. Confirm that Slurm is available:

```bash
hostname
sinfo
```

If `sinfo` errors, or the scheduler/login node is failed, stop and resolve the CycleCloud/quota issue before continuing.

## 4. Get the small demo files onto the login node

In the Linux login-node terminal, try:

```bash
git clone https://github.com/karris12/bankofcanada.git
cd bankofcanada
ls
```

You should see `README.md`, `docs`, and `workload`. The files must be in a directory shared with compute nodes. Check that the selected HTC partition can run a basic command and read the program:

```bash
srun --partition=htc --nodes=1 --ntasks=1 hostname
srun --partition=htc --nodes=1 --ntasks=1 test -r "$PWD/workload/estimate_pi.py"
echo $?
```

The first command may wait while CycleCloud starts the one HTC worker. The second check should print exit code `0`. If it fails, move the repository to the deployment's shared home/work folder and repeat. If it reports quota or node failure, stop and resolve that issue; don't keep submitting jobs.

If `git clone` fails because the node cannot reach GitHub, use an administrator-approved file-transfer method. Don't add an unpriced NAT gateway or open the cluster to the public internet just for this demo.

## 5. Submit one job

From the repository directory on the login node, submit the job:

```bash
sbatch workload/demo.sbatch
```

Expected response:

```text
Submitted batch job 12345
```

Your job ID will differ. `sbatch` hands the script to Slurm; the job requests one CPU and one HTC node.

## 6. Check and read the result

Replace `12345` with the job ID printed above:

```bash
squeue --jobs 12345
sinfo --partition=htc
cat slurm-12345.out
```

`squeue` shows a job while it is queued or running. `PD` means pending, `R` means running. This small job may finish before you run `squeue`, so an empty result is normal. `sinfo` shows the partition's available nodes.

The `cat` command prints the saved job output. It should look like:

```text
Slurm job ID: 12345
Compute node: htc-...
Points: 5000000
Points inside circle: ...
Estimated pi: 3.14...
Elapsed seconds: ...
```

The exact node name, point count, pi estimate, and elapsed time vary. A result near `3.14` means the program ran successfully. The output file is named `slurm-<job-id>.out`.

If the job failed and accounting is enabled, inspect it with:

```bash
sacct --jobs 12345 --format=JobID,State,ExitCode
```

If accounting is disabled, which is fine for this demo, check the saved output and CycleCloud's node issues instead. You do not need a database or `sacct` to run a Slurm job.

## 7. Explain it in the interview

> “I submitted one Python workload using `sbatch`. Slurm placed it in the HTC partition on one CPU worker. I monitored it with `squeue` and `sinfo`, then read the job's saved output. CycleCloud manages the Azure cluster lifecycle, and Slurm manages job scheduling.”

If asked what makes it HPC: explain that this tiny example is a **first Slurm operations demo**, not a performance benchmark. Real HPC work would need representative parallel code, appropriate CPU/network/storage sizing, measured scaling, and cost-per-job analysis.

## 8. Clean up

After the demo, cancel only your own still-running job if necessary:

```bash
scancel YOUR_JOB_ID
```

In CycleCloud, terminate the Slurm cluster to remove its worker/scheduler resources when no longer needed. To stop charges for the whole experiment, also delete the **dedicated** `rg-hpc-interview-demo` resource group in Azure portal—but only after confirming it contains no unrelated resources. Recheck Cost Management and the resource list afterward. Costs already incurred are not refunded.

## Official references

- [CycleCloud Slurm 4 overview](https://learn.microsoft.com/azure/cyclecloud/slurm-4?view=cyclecloud-8)
- [Connect to a login node through Bastion](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-login-node-with-bastion?view=cyclecloud-8)
- [Azure quota requests](https://learn.microsoft.com/azure/quotas/per-vm-quota-requests)

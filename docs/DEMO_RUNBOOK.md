# Start-to-finish guide: the tiny CycleCloud + Slurm demo

This guide is written for a first Slurm demo. It uses one Python program and one Slurm job:

1. Estimate pi with randomly generated points.
2. Ask Slurm to run the program on **one HTC worker node**.
3. Check the job and read its output.

It does not use a job array, a database, extra Python packages, or real financial data.

## Important: your Azure workspace already exists

You have already provisioned `rg-hpc-interview-demo` in East US, the CycleCloud VM (`ccw-cyclecloud-vm`), the network, storage, and a Bastion. **Do not create another CycleCloud Workspace or delete this resource group just to restart the demo.** Those resources can cost money while you work on the Slurm quota issue.

Your latest Azure error said:

```text
Current regional core limit: 4
Current usage:               4
Failed VM needs:             4 additional cores
Minimum limit for that VM:   8
```

The CycleCloud VM is `Standard_D4as_v4`, which uses 4 vCPUs. Azure has no regional quota left for the failed Slurm VM. The error's 8-core limit is only enough to cover the existing 4-core VM plus that one requested 4-core VM. It does **not** prove there will be quota left for an HTC worker.

**First get a quota increase approved, and check cost. Don't press Retry or start additional VMs until that is done.** A quota request doesn't run VMs, but the VMs and Bastion may accrue charges when running. A Cost Management budget is an alert, not a hard spending cap.

## Step 1: Prepare the simplified project on your Windows computer

The project is already in your local repository. Open **Windows PowerShell** and run:

```powershell
Set-Location "$HOME\Documents\devopsProject\hpc"
git pull
python --version
python -m unittest discover -s tests -v
python workload\estimate_pi.py --points 10000 --seed 42
```

The tests should finish with `OK`.

Expected output looks like this:

```text
Points: 10000
Points inside circle: 7815
Estimated pi: 3.126000
Elapsed seconds: 0.01
```

Your elapsed time may differ. This checks Python and the demo locally, without Azure.

## Step 2: Check the Azure deployment and calculate the quota you need

Use the Azure portal. Make sure the selected subscription is the one containing `rg-hpc-interview-demo`.

1. Open **Resource groups** > `rg-hpc-interview-demo` > **Resources**. Identify the CycleCloud VM, Bastion, and any Slurm scheduler or login VMs.
2. In CycleCloud, select the failed node and record its **VM size and vCPU count**. Check any other scheduler/login node sizes too.
3. For this simple demo, plan for **one HTC worker maximum**, using the smallest suitable CPU VM available in East US. Do not start HPC, GPU, a second worker, or optional databases.
4. Add up the vCPUs of all VMs that must be running at the same time: the current CycleCloud VM plus the Slurm scheduler/login VMs plus one HTC worker. Compare the total to **Total Regional vCPUs**. Also check the quota for the VM family used by the selected worker and scheduler. Azure enforces both regional and VM-family quotas.
5. In Azure portal search for **Quotas** > **Compute**. Select **East US** and review **Total Regional vCPUs** and the relevant VM-family quota. Request a limit that covers the total you calculated—not merely the `8` cores in the original failure. Ask your subscription administrator to submit/approve the request if your account can't do it.
6. Wait for the quota request to show as approved, then check the quota page again. If the quota is denied, ask the administrator about another supported region or stop the cloud demo; do not keep retrying the node.
7. Check **Cost Management + Billing** and confirm the remaining credit and expiration date. Price the already-running CycleCloud VM and Bastion plus the planned scheduler/login and one worker. If the full run is not comfortably affordable within your credit, stop and use the local demo.

Microsoft's instructions: [request an Azure VM quota increase](https://learn.microsoft.com/azure/quotas/per-vm-quota-requests) and [plan a CycleCloud Workspace deployment](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8).

## Step 3: Set a small Slurm cluster limit

Open the CycleCloud web page that you already accessed at `https://localhost:8443`. Find the existing cluster (your dashboard previously showed a cluster named `ccw`) and its failed node. **Do not create a second workspace.**

1. Confirm this existing cluster uses the **Slurm** template. If it does not, stop and ask before creating a new cluster.
2. Open **Edit** for the Slurm cluster.
3. Choose a small CPU-only execute VM supported by your quota.
4. Set the **HTC maximum to 1 node**. If the form has a core limit instead, use the worker VM's vCPU count as the limit for one worker. This demo needs one CPU for its job, but Azure quota counts the full VM's vCPUs.
5. Set GPU capacity to zero. Set HPC capacity to zero if allowed; otherwise leave its minimum and don't use the HPC partition.
6. Leave Slurm job accounting off. This demo does not need `sacct` or a separately configured MySQL database.
7. Save the edits. Recheck the VM sizes and HTC cap. Watch the resource group and Cost Management for unexpected resources.

If you cannot identify a hard maximum of one HTC worker or confirm the VM sizes, stop rather than guessing.

## Step 4: Retry and wait for healthy nodes

Only continue once quota is approved and the cluster settings are correct.

1. In CycleCloud, select the failed Slurm node and use **Retry**. Don't retry the CycleCloud VM itself if it is already running.
2. Watch the node state. It may show **Acquiring**, then **Preparing**, then **Ready/Started** while Azure creates and configures it.
3. Check **Issues** or the node event log if it fails again. Stop and read the new error before retrying.
4. Before running the job, make sure the Slurm scheduler and login/authentication node are ready, and no required node is failed.

The CycleCloud UI's overall cluster state alone does not prove every node is healthy. A previous dashboard showed `1 failed` and `0 instances`; that cluster was not ready for jobs.

## Step 5: Connect to the Slurm login node

Do **not** run `sbatch` in Windows PowerShell, in the CycleCloud web page, or on the CycleCloud application VM. Run Slurm commands in a Linux terminal on the **Slurm login/authentication node**.

From the CycleCloud page, select the **login/authentication node**, open its details, and copy its VM **ResourceId**. Use the login node's ID—not the CycleCloud VM ID and not the scheduler's network interface ID.

Open Windows PowerShell. Sign into Azure and select the subscription used by the workspace:

```powershell
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
az account show --output table
```

Start an SSH connection through your Bastion. Use the actual login-node resource ID, and make sure the SSH key path points to your private key on this computer:

```powershell
az network bastion ssh `
  --name "bastion" `
  --resource-group "rg-hpc-interview-demo" `
  --target-resource-id "PASTE_LOGIN_NODE_RESOURCE_ID" `
  --auth-type ssh-key `
  --username "hpcadmin" `
  --ssh-key "$HOME\.ssh\hpc-interview-demo"
```

Use your deployment's actual username/key path if different. The command should open a Linux shell. **Keep the private key private**; never paste it into chat or put it in GitHub.

Check that you reached the login machine and Slurm is responding:

```bash
hostname
sinfo
```

If `sinfo` errors, the Slurm scheduler isn't ready. Go back to CycleCloud and resolve the node issue; don't continue submitting jobs.

## Step 6: Download the project to the login node

In the Linux terminal, use your shared home directory so compute nodes can read the job script:

```bash
cd "$HOME"
git clone https://github.com/karris12/bankofcanada.git
cd bankofcanada
ls
```

You should see `README.md`, `docs`, `tests`, and `workload`. If you already cloned it in this home folder, use `cd "$HOME/bankofcanada"` and then `git pull` instead of cloning again.

Check that Slurm can run a tiny command on an HTC worker and that the worker can read the Python script:

```bash
srun --partition=htc --nodes=1 --ntasks=1 hostname
srun --partition=htc --nodes=1 --ntasks=1 test -r "$PWD/workload/estimate_pi.py"
echo $?
```

The first command may take time while the HTC worker starts. The final output should be `0`. If it reports a quota, VM, or failed-node problem, stop and investigate in CycleCloud. If the final result is nonzero, the files are not on shared storage; follow your administrator's instructions for the shared home/work directory.

If `git clone` fails because the login node can't reach GitHub, don't add an unpriced NAT gateway just for this demo. Ask your administrator for an approved file-transfer method.

## Step 7: Submit the one-job Slurm demo

From the `bankofcanada` directory on the login node:

```bash
sbatch workload/demo.sbatch
```

Slurm responds with a job ID, for example:

```text
Submitted batch job 12345
```

The actual ID will be different. The job script requests **one node, one task, one CPU, in the HTC partition**, and writes output to `slurm-<job-id>.out`.

## Step 8: Monitor the job and show its output

Replace `12345` with the job ID Slurm returned:

```bash
squeue --jobs 12345
sinfo --partition=htc
cat slurm-12345.out
```

`squeue` displays the job while pending or running. `PD` means pending and `R` means running. The job is small, so it may finish before you check; an empty `squeue` result is okay. The output file is the record of the completed job.

Expected output shape:

```text
Slurm job ID: 12345
Compute node: htc-...
Points: 5000000
Points inside circle: ...
Estimated pi: 3.14...
Elapsed seconds: ...
```

The exact node name, point count, estimate, and elapsed time vary. A result near `3.14` means the calculation completed successfully. If the file is missing or doesn't contain these lines, inspect CycleCloud **Issues** and the Slurm job state before retrying.

You do not need job accounting or `sacct` for this first demo. The proof is: `sbatch` accepted the job, the output names the HTC compute node, and the program printed its pi estimate.

## Step 9: Explain what you demonstrated

You can say:

> “I submitted one Python job with `sbatch`. Slurm scheduled it on one CPU in the HTC partition. I checked the queue with `squeue`, viewed the partition with `sinfo`, and read the job output. CycleCloud manages Azure cluster lifecycle; Slurm schedules the workload.”

This is a simple Slurm operations demo, not a performance benchmark. You don't need to claim the pi program is a large-scale HPC workload.

## Step 10: Stop costs when you finish

1. Check for your job: `squeue -u "$USER"`. If it is still running, cancel only your demo job with `scancel YOUR_JOB_ID`.
2. In CycleCloud, terminate the Slurm cluster so worker/scheduler machines are removed or deallocated.
3. Remember that terminating the Slurm cluster does **not** remove the CycleCloud workspace VM or Bastion.
4. To end charges for this experiment, delete `rg-hpc-interview-demo` **only if you confirm it contains no unrelated resources and you no longer need the workspace**. In the Azure portal: **Resource groups** > `rg-hpc-interview-demo` > **Delete resource group**. Type the resource-group name to confirm.
5. Review the resource group and Cost Management for leftover resources. Deleting Azure resources does not refund charges already accrued.

## If starting from a completely new Azure subscription

You do **not** need this section for your current deployment. It already has the workspace, network, storage, CycleCloud VM, and Bastion. Do not follow these steps to create a duplicate.

For a brand-new deployment, first check credit, permissions, and pricing as in Step 2. Then follow Microsoft's current [CycleCloud Workspace for Slurm deployment guide](https://learn.microsoft.com/azure/cyclecloud/overview-ccws?view=cyclecloud-8) and [deployment planning checklist](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8). Create a **new dedicated resource group** and a greenfield Workspace. Use only a secure login method you understand and have priced. Use a public SSH key, never a private key. Do not continue through an Entra, role-assignment, network, or cost prompt you don't understand. After deployment, follow Steps 3–10 here to create/configure Slurm, connect, run the job, and clean up.

## Official Azure references

- [CycleCloud Workspace for Slurm overview](https://learn.microsoft.com/azure/cyclecloud/overview-ccws?view=cyclecloud-8)
- [CycleCloud Workspace deployment planning](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8)
- [Azure quota increase instructions](https://learn.microsoft.com/azure/quotas/per-vm-quota-requests)
- [Connect to a login node through Bastion](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-login-node-with-bastion?view=cyclecloud-8)
- [Start a CycleCloud cluster](https://learn.microsoft.com/azure/cyclecloud/how-to/start-cluster?view=cyclecloud-8)

# Beginner's walkthrough: CycleCloud + Slurm interview demo

This guide takes you from a Windows computer to a small Slurm job running on Azure. Read it once before starting. Azure CycleCloud is real cloud infrastructure, not a free simulation; the walkthrough does **not** deploy anything for you.

## The finished demo

You will run four small independent computer simulations. Slurm schedules them as one job array. CycleCloud provides the cluster and can start compute capacity for the queued work. A final command combines the results.

```text
Your Windows computer
       | browser / secure sign-in
       v
Azure CycleCloud workspace
       | controls the cluster
       v
Slurm scheduler  --->  up to 2 CPU compute nodes
       | submits four small tasks
       v
Four JSON results  --->  one summary
```

The model uses **invented data** and a simplified relationship between interest-rate changes and portfolio value. It is a teaching example, not a Bank of Canada model, a market forecast, or financial advice.

## Important: should you deploy to Azure?

The Azure Marketplace route is convenient, but it provisions **multiple billable resources**: at least a CycleCloud virtual machine, storage, and networking, plus cluster/login/compute resources as you create the Slurm cluster. Secure login through Azure Bastion may add more charges. Marketplace terms, your region, and credit expiry also matter. An idle cluster is not the same as a deleted deployment.

**Do not click Create until you have checked the estimate.** We cannot tell whether your $180 will cover the deployment: Azure prices, region, VM size, Bastion choice, and unexpired credit are specific to your account.

If you cannot confirm a comfortably affordable estimate, required permissions, and a safe way to connect, **stop here**. Run the local demo in section 1 and present the cloud architecture and runbook at the interview instead. That is better than accidentally spending your credits.

Before any deployment:

1. In the [Azure portal](https://portal.azure.com), select the right directory and subscription. Check the remaining credit and expiration date in **Cost Management + Billing**.
2. In [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/), estimate the full deployment for the region you intend to use. Include CycleCloud, scheduler/login/compute VMs, disks, network resources, and any Bastion, NAT, Marketplace, or storage charges.
3. Ask your subscription administrator whether you are allowed to deploy this solution. Microsoft's [deployment checklist](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8) describes subscription roles and Microsoft Entra app-registration requirements. If you do not have the needed permissions or do not understand an app-registration prompt, stop and ask the administrator. Do not change your role or bypass an organization policy.
4. A Cost Management budget can email you an alert; it does **not** stop the deployment or cap charges. Continue checking Cost Management while resources exist.

This deployment also uses an SSH key for secure login. Before beginning, open Windows PowerShell and check whether you already have a key that you can use. If not, create a dedicated key pair:

```powershell
ssh-keygen -t rsa -b 4096 -f "$HOME\.ssh\hpc-interview-demo"
Get-Content "$HOME\.ssh\hpc-interview-demo.pub"
```

If that key filename already exists, do not overwrite it; choose another filename instead. When asked for a passphrase, you can set one and keep it safe. Provide only the displayed `.pub` **public key** to the deployment form. Keep the file without `.pub` private on your computer; never upload it to GitHub or share it.

The Marketplace form changes over time and by subscription. Treat the current offer's price, terms, and form—not screenshots or this example—as authoritative.

## 1. Check the project locally first (Windows PowerShell)

Do this from your local clone before provisioning anything. Open **PowerShell** in the project folder:

```powershell
Set-Location "$HOME\Documents\devopsProject\hpc"
python --version
python -m unittest discover -s tests -v
```

Expected shape of output (timings and Python version will differ):

```text
Python 3.x.x
...
Ran 5 tests in ...s

OK
```

Now run four small local tasks and combine them. This checks the workload without Azure:

```powershell
New-Item -ItemType Directory -Force results | Out-Null
for ($task = 0; $task -lt 4; $task++) {
  python workload/simulate_rate_risk.py `
    --samples 1000 `
    --seed (20261025 + $task) `
    --output "results/local-$task.json"
}
$files = Get-ChildItem results\local-*.json | ForEach-Object { $_.FullName }
python workload/aggregate_risk.py @files
```

Expect four `seed=... samples=1000 ...` lines, followed by a summary:

```text
Completed tasks: 4
Monte Carlo samples: 4000
Mean loss: $...
95th percentile loss (VaR proxy): $...
Mean loss in 95th percentile tail: $...
Sum of worker compute seconds: ...
```

The dollar amounts are **synthetic results** and will depend on the sample count and seeds. Seeing `Completed tasks: 4` confirms all four local files were combined.

## 2. Provision the workspace in the Azure portal

Only continue if the checks above pass and your full estimate is affordable. This is the **workspace deployment**—it gives you CycleCloud. You will create the Slurm cluster separately in step 4.

1. Open [portal.azure.com](https://portal.azure.com). Check the directory and subscription shown in the top-right/account area.
2. Select **Create a resource** or open **Marketplace**, search for the exact offer **Azure CycleCloud Workspace for Slurm**, and verify the publisher, plan, terms, and any displayed charges.
3. Select **Create**. In the deployment form, fill the subscription, a new dedicated resource group such as `rg-hpc-interview-demo`, and an available region. A resource group is just a named container for this demo's Azure resources.
4. Select the **greenfield/new environment** option if the form offers a choice. This creates the supporting network and resources for you. Do not choose brownfield/existing infrastructure unless you already have the network and storage and know how to configure them.
5. Review identity, authentication, network, and access sections. Supply the `.pub` public key from the previous section if requested. If the form requests an application ID or other Entra registration values and you do not already have an approved registration, stop and ask the administrator. See Microsoft's [Entra app registration guide](https://learn.microsoft.com/azure/cyclecloud/how-to/create-app-registration?view=cyclecloud-8); do not guess values.
6. Review the login method carefully. Azure CycleCloud Workspace for Slurm does not open an SSH route from your computer by default. Some deployments offer Azure Bastion; if you plan to use the documented SSH workflow in this guide, check whether Bastion is included and price it. If no supported secure login method is included—or the Marketplace form does not make it clear—stop and ask your administrator how you will connect and what that will cost. Never open SSH to the internet.
7. Leave optional GPU, Azure NetApp Files, Azure Managed Lustre, high availability, Open OnDemand, and other add-ons off for this basic demo unless you specifically need and have priced them. If NAT or another outbound networking option is needed to download code, include that cost too. Alternatively, transfer the repository by an approved method rather than enabling unpriced network access.
8. Review every page and the final **Review + create** screen. Confirm the right subscription, resource group, region, estimated costs/terms, and required permissions. If anything is unexpected, choose **Previous** or cancel. Only press **Create** after this final check.
9. In Azure portal, open **Resource groups** > `rg-hpc-interview-demo` > **Deployments**. Wait for the workspace deployment status to become **Succeeded**. Provisioning may take several minutes.

What success looks like: deployment status **Succeeded** and resources for the CycleCloud workspace visible in the dedicated resource group. If deployment says **Failed**, read the deployment error; do not repeatedly retry. Common blockers are permission, Entra setup, quota, region capacity, or policy. Ask the subscription administrator about the specific error.

**Do not delete the resource group yet:** it is needed for the demo. You will delete it in the cleanup section.

## 3. Open CycleCloud

The workspace and the Slurm cluster are different things:

- The **workspace** is the CycleCloud application and its supporting Azure infrastructure.
- The **Slurm cluster** is a set of scheduler, login, and compute machines managed by CycleCloud.

Find the CycleCloud access details in the deployment's **Outputs** or the Microsoft instructions linked below. Sign in through the method the deployment provides. If the CycleCloud web portal is not reachable directly, follow Microsoft's [Bastion tunnel instructions](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-portal-with-bastion?view=cyclecloud-8); that procedure uses an Azure CLI tunnel and opens `https://localhost:8443` in your browser.

Do **not** guess a URL, username, or password, and do not make the CycleCloud VM or SSH port public to work around a connection problem. Stop and use the supported connection instructions for your deployment.

## 4. Create and start the Slurm cluster

In the CycleCloud web portal:

1. Open **Clusters** and choose **Add**. Select the supplied **Slurm** template. If Slurm is not offered, do not choose another scheduler; stop and follow the official [Slurm 4 project setup](https://learn.microsoft.com/azure/cyclecloud/slurm-4?view=cyclecloud-8) or ask for help.
2. Enter a short cluster name such as `interview-slurm`. Cluster names are also used in commands, so use the same spelling later.
3. Select the subscription credentials, region, and virtual-network/subnet associated with the workspace. If the form doesn't show these choices, or the only choices refer to a different subscription/network, stop rather than guessing.
4. In the cluster parameters, choose a small **CPU-only** execute VM available in this region. Use the `hpc` partition for this demo. Set its autoscaling limit to **no more than 4 total compute cores** (not 4 nodes). This is the safety limit; it will normally allow no more than two 2-core worker VMs. Keep GPU capacity at zero. Parameter names vary across Slurm template versions; look for **Max HPC Cores**, **Max Cores**, or the equivalent limit, and verify the selected VM's core count. If you cannot find a way to impose a low hard limit, do not start the cluster.
5. Use only the minimum storage and login options required by the template; leave optional high-performance filesystems and databases disabled for this short job. Review the form for optional billable resources.
6. Select **Save** to create the cluster definition. Saving a definition is not the same as starting its VMs. Recheck its VM type and core/node cap in **Edit** before starting.
7. Select **Start** and confirm. CycleCloud requests and configures the cluster VMs. Wait for the scheduler and login nodes to reach their ready/started state. Provisioning can take several minutes; VM quota or capacity can delay or prevent startup.
8. Watch Azure Cost Management and the resource group while starting. If you see an unexpected VM size, extra service, or resource count, stop and investigate.

CycleCloud's Slurm 4 template includes partitions such as `hpc`, `htc`, `gpu`, and `dynamic`. For this project, submit to `hpc` only. The job script limits the array to two concurrently running tasks; the cluster's separate four-core limit caps compute capacity.

## 5. Connect to the login node

Run the HPC commands on the **Linux Slurm login node**, not in Windows PowerShell, not in the Azure portal's local browser, and not on the CycleCloud application VM.

For Azure CycleCloud Workspace, Microsoft's [login-node Bastion guide](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-login-node-with-bastion?view=cyclecloud-8) describes connecting by SSH through Bastion. It requires the private SSH key matching the public key supplied at deployment. Keep that private key on your own computer; never put it in Git or paste it into chat.

On your Windows computer, open a **second PowerShell window** (leave the browser open). If needed, install the [Azure CLI for Windows](https://learn.microsoft.com/cli/azure/install-azure-cli-windows), then sign in and select the same subscription used for the workspace:

```powershell
az login
az account set --subscription "YOUR_SUBSCRIPTION_NAME_OR_ID"
az account show --output table
```

`az account show` should display the intended subscription. The official guide gets the login-node **resource ID** from the CycleCloud UI and uses `az network bastion ssh`. In CycleCloud, select the authentication/login node, open its details, choose the **VM** tab, and copy `ResourceId`. Run:

```powershell
az network bastion ssh `
  --name "YOUR_BASTION_NAME" `
  --resource-group "rg-hpc-interview-demo" `
  --target-resource-id "PASTE_LOGIN_NODE_RESOURCE_ID" `
  --auth-type ssh-key `
  --username "hpcadmin" `
  --ssh-key "$HOME\.ssh\hpc-interview-demo"
```

Replace the Bastion name, resource group, resource ID, username, and key path with the actual values in your workspace. If `az network bastion ssh` is unavailable or connection fails, use Microsoft's guide for your deployed version—do not open SSH to all internet addresses.

Once connected, the terminal prompt should be a Linux shell on the login node. Check which host you are on:

```bash
hostname
whoami
```

Keep that SSH terminal open for the next steps.

## 6. Put the demo files on the login node

In the login-node Linux terminal:

```bash
git clone https://github.com/karris12/bankofcanada.git
cd bankofcanada
pwd
ls
```

Expected `ls` output includes `README.md`, `docs`, `tests`, and `workload`.

If `git clone` reports a network/DNS error, the login node might not have outbound internet access. Do not enable broad network access just to fix this. Use an approved file-transfer/VS Code route for your environment or ask your administrator how to transfer the repository.

Check that the scheduler can run a command on a compute node and read the script from this directory:

```bash
srun --partition=hpc --nodes=1 --ntasks=1 hostname
srun --partition=hpc --nodes=1 --ntasks=1 test -r "$PWD/workload/simulate_rate_risk.py"
echo $?
srun --partition=hpc --nodes=1 --ntasks=1 python3 --version
```

Expected: `hostname` prints a compute-node name; `echo $?` prints `0`; Python prints a version. The first `srun` might wait while CycleCloud provisions an execute node. If the script check fails, the login-node directory is not visible to compute nodes. Stop here and ask how to use the shared home/work directory for this deployment; do not submit the array from a non-shared folder.

## 7. Submit the Slurm job and inspect it

Still in the Linux login-node terminal, from the `bankofcanada` repository directory:

```bash
mkdir -p results
sbatch --partition=hpc workload/slurm_array.sbatch
```

Expected response:

```text
Submitted batch job 12345
```

Your number will differ. Copy it; below, replace `12345` with **your** job ID.

While the job is queued or running, inspect it:

```bash
squeue --jobs 12345
sinfo --partition=hpc
```

Illustrative output (states and node names vary):

```text
JOBID  PARTITION  NAME       USER       ST  TIME  NODES  NODELIST(REASON)
12345  hpc        rate-risk  hpcadmin   R   0:04  1      ...
```

`ST` is the job state: `PD` means pending, `R` means running. A very short job may finish before you run `squeue`; an empty queue can mean it has completed, so continue to the completion checks.

The Slurm script runs four tasks (`0` to `3`) with at most two running concurrently. By default each task uses 100,000 samples. To make the run last a little longer for a live demo, submit **one** bounded array with 500,000 samples per task:

```bash
SAMPLES_PER_TASK=500000 sbatch --partition=hpc workload/slurm_array.sbatch
```

If you use this second command, copy and use its newly returned job ID instead. Do not repeatedly submit jobs or raise the four-core cluster limit to make the demo look busier.

## 8. Confirm completion and show the result

Replace `12345` with your job ID:

```bash
sacct --jobs 12345 --format=JobID,JobName%18,State,Elapsed,AllocCPUS,NodeList,ExitCode
ls results/12345_*.json
python3 workload/aggregate_risk.py results/12345_*.json
```

If `sacct` is enabled, look for four array task rows ending in `COMPLETED` with exit code `0:0`. The file listing should show four result files. The aggregate command should print:

```text
Completed tasks: 4
Monte Carlo samples: 400000
Mean loss: $...
95th percentile loss (VaR proxy): $...
Mean loss in 95th percentile tail: $...
Sum of worker compute seconds: ...
```

With the optional 500,000 setting, the sample count is `2000000` instead. The monetary values vary by seed and samples. The worker seconds are the sum of the tasks' measured simulation time, **not** the total Azure bill or complete wall-clock time.

If `sacct` says accounting is unavailable, do not add a billable database just for the demo. Check each task log and output instead:

```bash
ls rate-risk-12345_*.out
ls results/12345_*.json
```

Use the actual job ID in both commands. If there are not exactly four JSON results, or the reducer reports an error, check the Slurm `.out` files before claiming success.

## 9. End the demo and remove Azure charges

Do this as soon as you have captured the output you want:

1. On the login node, check whether anything is still queued or running: `squeue -u "$USER"`. Cancel only your own demo jobs if necessary: `scancel YOUR_JOB_ID`.
2. In CycleCloud, select the `interview-slurm` cluster and choose **Terminate** (or the version's corresponding stop/delete action). Confirm the cluster's execute VMs have been terminated/deallocated. Stopping the cluster does **not** delete the CycleCloud workspace.
3. In Azure portal, open **Resource groups** > `rg-hpc-interview-demo`. Confirm every listed resource belongs only to this demo.
4. When you are certain the group contains no unrelated work, select **Delete resource group**, type the resource group name, and confirm. This removes the workspace and its resources. Never delete a shared or pre-existing resource group.
5. Reopen the resource group list and Cost Management to check for remaining resources/charges. Some linked or Marketplace resources may have been created outside the group; clean up only items you can positively identify as belonging to this demo.

Deleting the cluster alone does **not** remove the CycleCloud workspace. To stop ongoing costs for the entire experiment, remove the dedicated resource group after the demo. Costs that already accrued are not refunded by deleting resources.

## 10. Five-minute interview explanation

1. **Architecture:** CycleCloud manages cluster lifecycle; Slurm schedules work; login/scheduler roles are separate from elastic compute.
2. **Parallel work:** The four array tasks run independent simulations with separate, repeatable random seeds; the reducer calculates statistics across all task results.
3. **Live result:** Show `sbatch`, `squeue` or `sacct`, four output files, and the reducer summary. Explain that starting cloud VMs can take longer than this tiny workload.
4. **Cost and security:** Show the four-core compute cap, private login path, synthetic data, Cost Management checks, and teardown.
5. **Limitations:** State that this is not a validated financial model. For real HPC you would benchmark representative code, measure startup and storage/network effects, validate results, monitor cost per completed job, and test failures.

## Troubleshooting: what to do next

| What you see | What it usually means | Next step |
|---|---|---|
| Marketplace asks for permissions you do not have | Your account cannot assign the roles needed for deployment | Stop and ask the subscription administrator. Do not work around it. |
| A quota, capacity, or SKU error | That VM is unavailable or not permitted in this region | Stop; check quota with the administrator. Do not switch to a much larger or unpriced VM. |
| No Slurm template in CycleCloud | The template was not installed/imported, or workspace provisioning is incomplete | Stop; use the official [Slurm 4 instructions](https://learn.microsoft.com/azure/cyclecloud/slurm-4?view=cyclecloud-8). Do not create an unrelated cluster. |
| SSH/Bastion connection fails | Missing/mismatched key, Bastion setup, or access configuration | Follow the official [login-node access guide](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-login-node-with-bastion?view=cyclecloud-8); never expose public SSH. |
| `srun` waits or reports no nodes | The cluster is still starting, has zero configured capacity, or has a quota issue | Check the cluster state in CycleCloud and the Slurm partition with `sinfo`; wait for startup, then ask for help if it fails. |
| `srun test` returns nonzero | The repository folder is not visible on compute nodes | Move the project to the deployment's shared home/work filesystem and repeat the test before submitting jobs. |
| `sacct` is unavailable | Slurm job accounting is not configured | Inspect task `.out` files and result files. Do not add a database for this demo. |

## Official documentation

- [Azure CycleCloud Workspace for Slurm overview](https://learn.microsoft.com/azure/cyclecloud/overview-ccws?view=cyclecloud-8)
- [Plan a CycleCloud Workspace deployment](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8)
- [Deploy the workspace using Azure CLI](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/deploy-with-cli?view=cyclecloud-8) (advanced; this guide uses the portal)
- [Connect to the CycleCloud portal through Bastion](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-portal-with-bastion?view=cyclecloud-8)
- [Connect to a Slurm login node through Bastion](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-login-node-with-bastion?view=cyclecloud-8)
- [CycleCloud Slurm 4 operations](https://learn.microsoft.com/azure/cyclecloud/slurm-4?view=cyclecloud-8)
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)

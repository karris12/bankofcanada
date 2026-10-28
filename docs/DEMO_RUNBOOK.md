# Start from scratch: tiny Azure CycleCloud + Slurm demo

This guide assumes **you deleted the previous workspace and its resources**. It builds one small Slurm demo from the beginning:

1. Estimate pi using a simple Python program.
2. Submit that program as one Slurm job to one HTC CPU worker.
3. Check the job and read its output.

No job arrays, databases, GPU nodes, financial data, or extra Python packages are needed.

## Before Azure: know the quota blocker

Deleting Azure resources does **not** reset quota. Your last quota error showed:

- East US regional vCPU limit: **4**
- At the time of the error, usage: **4** (those resources are now deleted, so usage should have fallen; verify it in the portal)
- A failed VM needed **4 more** vCPUs
- Azure said the regional quota had to be at least **8** for that one VM request

The CycleCloud VM previously selected was `Standard_D4as_v4` (4 vCPUs). If you select it again, it can use your entire current 4-vCPU quota before you start Slurm. The Slurm scheduler/login VM and one HTC worker need additional quota. **Do not begin deployment or retry VM creation until you have checked and requested enough quota for every VM that must run at once.**

Azure uses both a **total regional vCPU quota** and **per-VM-family quotas**. Check both. Add up the vCPUs of the CycleCloud VM, scheduler, login/authentication node(s), and one HTC worker based on the sizes shown by the current deployment form. Request a regional limit above that total, with a little headroom, and raise the relevant VM-family limit(s) too. There isn't one guaranteed number for every form/version. The old minimum of 8 only covered the VM from that specific failure; it is not a complete Slurm-cluster quota estimate.

If quota cannot be increased, or the sizes/cost aren't clear, stop and run the local demo in Step 1 rather than provisioning VMs that will fail.

## Step 1: Run the project locally on Windows

Open Windows PowerShell in your local repository:

```powershell
Set-Location "$HOME\Documents\devopsProject\hpc"
git pull
python --version
python -m unittest discover -s tests -v
python workload\estimate_pi.py --points 10000 --seed 42
```

The tests should finish with `OK`. The program's output should look like this; small differences are normal:

```text
Points: 10000
Points inside circle: 7815
Estimated pi: 3.126000
Elapsed seconds: 0.01
```

The program generates points in a square and counts how many land inside a circle. `4 × (points inside the circle / total points)` gives an estimate of pi, about 3.14. This is a tiny sample workload to practice Slurm, not a performance benchmark.

## Step 2: Check subscription, credit, permissions, and quota

In the [Azure portal](https://portal.azure.com):

1. Sign in to the correct directory and subscription. Confirm no old demo resources remain in Resource groups. Use a **new, dedicated** resource group for the fresh deployment.
2. Open **Cost Management + Billing**. Check remaining credit and its expiration date. An Azure budget sends alerts; it does not cap or stop spending.
3. Open **Quotas** → **Compute** → choose **East US** (or another region you intend to use). Check **Total Regional vCPUs** and the VM-family quota(s) for the sizes you plan to use.
4. Request quota for the complete VM plan: CycleCloud + Slurm scheduler + login/authentication node(s) + one HTC worker. Include modest headroom. Wait until the portal shows the quota increase approved, and verify the new limits. Do not rely on the previous failed-deployment estimate alone.
5. Estimate the full deployment in the [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/). Include the CycleCloud VM, Slurm VMs, one worker, disks/storage, network components, and Bastion if using it. Marketplace terms and prices depend on your offer, region, and subscription. If the estimate does not comfortably fit your remaining credit, stop.
6. Confirm you have permission to deploy the solution and create its role assignments. The current Microsoft planning guide lists subscription `Contributor` and `User Access Administrator` roles. Ask your subscription administrator if you lack a role or don't understand a prompt; don't work around access policy.

Official references: [request VM quota](https://learn.microsoft.com/azure/quotas/per-vm-quota-requests), [plan a CycleCloud Workspace for Slurm deployment](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8).

## Step 3: Prepare identity and SSH access

The current CycleCloud Workspace planning guide requires a Microsoft Entra application registration. Ask your administrator whether one is already approved for CycleCloud. If not, follow the official [CycleCloud Entra app registration guide](https://learn.microsoft.com/azure/cyclecloud/how-to/create-app-registration?view=cyclecloud-8) with an administrator. The guide contains settings such as application roles and redirect URIs; do not guess those values.

Create a dedicated SSH key on your computer if you don't already have a key for this demo. In PowerShell:

```powershell
ssh-keygen -t rsa -b 4096 -f "$HOME\.ssh\hpc-interview-demo"
Get-Content "$HOME\.ssh\hpc-interview-demo.pub"
```

If the key file already exists, choose another filename; don't overwrite a key you use elsewhere. Put only the `.pub` **public key** in the deployment form. Keep the key file without `.pub` private on your computer. Never add either key to GitHub or send it in chat.

## Step 4: Deploy the CycleCloud Workspace from Azure Marketplace

The workspace provides the CycleCloud application and its supporting Azure resources. You configure/start the Slurm cluster separately afterward.

1. In the Azure portal, open **Marketplace** and search for the exact offer **Azure CycleCloud Workspace for Slurm**. Confirm the publisher, plan, terms, and current price.
2. Select **Create**. Use the correct subscription, a **new resource group** such as `rg-hpc-interview-demo`, and the region where quota was approved. Choose the **greenfield/new environment** option; brownfield is for an existing, intentionally configured network/storage setup.
3. Follow the form's identity and network sections. Enter only the approved Entra application values and the SSH **public** key when requested. If the form asks for unfamiliar role, identity, network, or authentication values, stop and ask your administrator before continuing.
4. For the options you asked about:
   - **Create a Bastion for SSH connections:** choose this only if you need it for secure access and have included its cost in your estimate. It provides a private access path; don't open SSH to the public internet as an alternative.
   - **Create a NAT Gateway:** leave it off unless the deployment requires outbound internet or you specifically need that feature and have priced it. If the login node can't download GitHub files later, use an approved transfer method instead of adding networking without checking cost.
   - **Peer to an existing virtual network:** leave it off for a standalone interview demo. Use it only if an administrator has provided a specific existing hub VNet to connect.
5. Keep optional GPU, Azure NetApp Files, Azure Managed Lustre, high availability, and Open OnDemand off unless the form requires them and you have priced them. Avoid optional paid storage/database services for this one-job demo.
6. Read every page of the form. On **Review + create**, check the subscription, resource group, region, VM sizes, roles, network options, and estimated costs again. If the estimate or a setting is unexpected, go back or cancel. Only click **Create** if the full design is affordable and understood.
7. In Azure portal, open the new resource group's **Deployments** page. Wait for the deployment to report **Succeeded**. If it fails, read the specific deployment error and resolve that cause before retrying.

The portal's offer and form may change. The displayed current offer and Microsoft's official [planning guide](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8) take precedence over this walkthrough.

## Step 5: Open the CycleCloud portal

Use the secure portal access method from the deployment. If the CycleCloud VM has no public IP, and Bastion was deployed, Microsoft documents a secure tunnel:

1. In Azure portal, open the CycleCloud VM (often named `ccw-cyclecloud-vm`) and copy its **VM Resource ID** from **Properties**.
2. In Windows PowerShell, sign in and choose the correct subscription:

   ```powershell
   az login
   az account set --subscription "YOUR_SUBSCRIPTION_ID"
   ```

3. Start the HTTPS tunnel. Replace the Bastion name/resource group if the deployment uses different names:

   ```powershell
   az network bastion tunnel `
     --name "bastion" `
     --resource-group "rg-hpc-interview-demo" `
     --target-resource-id "PASTE_CYCLECLOUD_VM_RESOURCE_ID" `
     --resource-port 443 `
     --port 8443
   ```

4. Leave PowerShell running and open **https://localhost:8443** in your browser. Sign in using the configured CycleCloud authentication. Your Azure sign-in may not be the same as your CycleCloud sign-in.

If Bastion was not deployed, don't make the CycleCloud VM public. Follow the approved connection method or stop and ask your administrator.

Official guide: [connect to the CycleCloud portal through Bastion](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-portal-with-bastion?view=cyclecloud-8).

## Step 6: Create and configure one Slurm cluster

In the CycleCloud portal:

1. Open **Clusters**. If the deployment already created a Slurm cluster, select it and inspect its settings; don't create a duplicate.
2. If no cluster exists, select **Add**, choose the **Slurm** template, and name it `interview-slurm`.
3. Choose the subscription credentials, region, VNet, and subnet created for this Workspace. If the correct choices aren't present, stop instead of guessing.
4. Choose a small CPU-only worker VM that is allowed by the approved quota. For this project set **HTC maximum = 1 node**. If the limit is cores, cap it at the selected worker VM's vCPU count. This job uses one CPU, but Azure quota counts the whole VM.
5. Set GPU capacity to zero. Set HPC capacity to zero if allowed; otherwise leave its minimum and do not submit work to HPC. The job is independent and belongs in the **HTC** partition.
6. Keep Slurm job accounting off. This demo doesn't need a database or `sacct`.
7. Select an Ubuntu image and use it consistently on the nodes if that image/version is supported by the selected CycleCloud Slurm template. Keep the Slurm version offered by the template unless Microsoft or your administrator specifies a compatible alternative.
8. Save the cluster definition. Reopen **Edit** and verify the worker type and one-node HTC cap before starting.
9. Select **Start** and wait for the required scheduler and login/authentication nodes to become **Ready/Started**. The HTC worker can be launched on demand by the job.
10. Check CycleCloud **Issues** and node events if any node fails. A cluster summary saying “Started” does not guarantee every node is healthy.

CycleCloud orchestrates Azure VMs; Slurm schedules the jobs that will run on the worker.

## Step 7: Connect to the Slurm login node

Slurm commands must run in a Linux shell on the **Slurm login/authentication node**—not in Windows PowerShell, the browser, or the CycleCloud application VM.

1. In CycleCloud, select the **login/authentication node** and open its details.
2. On the **VM** tab, copy that node's **ResourceId**. Do not use the CycleCloud VM's ID, the scheduler's network interface ID, or the worker ID.
3. On your computer, use the deployment's Bastion name, group name, username, and SSH private key to connect:

   ```powershell
   az network bastion ssh `
     --name "bastion" `
     --resource-group "rg-hpc-interview-demo" `
     --target-resource-id "PASTE_LOGIN_NODE_RESOURCE_ID" `
     --auth-type ssh-key `
     --username "hpcadmin" `
     --ssh-key "$HOME\.ssh\hpc-interview-demo"
   ```

   Replace values with the actual deployment settings. Keep the private key local.

4. In the resulting Linux terminal, verify the host and Slurm:

   ```bash
   hostname
   sinfo
   ```

If `sinfo` errors, stop and fix the scheduler/cluster before submitting a job.

Official guide: [connect to a Slurm login node through Bastion](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-login-node-with-bastion?view=cyclecloud-8).

## Step 8: Copy the project to shared storage

In the Linux login-node terminal, put the repository in your shared home directory so compute nodes can read it:

```bash
cd "$HOME"
git clone https://github.com/karris12/bankofcanada.git
cd bankofcanada
ls
```

You should see `README.md`, `docs`, `tests`, and `workload`. If already cloned, use `cd "$HOME/bankofcanada"` and `git pull` instead.

If GitHub access fails, use an administrator-approved file-transfer method. Don't add a NAT Gateway without checking cost and approval.

Confirm HTC can start a node and read the program:

```bash
srun --partition=htc --nodes=1 --ntasks=1 hostname
srun --partition=htc --nodes=1 --ntasks=1 test -r "$PWD/workload/estimate_pi.py"
echo $?
```

The hostname should be a compute node, and the final command should print `0`. If the job reports quota or failed-node errors, stop and inspect CycleCloud. If the file test fails, move the repository to the shared home/work directory.

## Step 9: Submit, monitor, and show the job

From the `bankofcanada` directory on the login node:

```bash
sbatch workload/demo.sbatch
```

Expected response:

```text
Submitted batch job 12345
```

Use the job ID that Slurm actually returned (here, `12345` is just an example):

```bash
squeue --jobs 12345
sinfo --partition=htc
cat slurm-12345.out
```

`PD` in `squeue` means pending; `R` means running. The job is short, so it may finish before you inspect the queue. An empty `squeue` output can be normal; read the job's output file.

Expected output shape:

```text
Slurm job ID: 12345
Compute node: htc-...
Points: 5000000
Points inside circle: ...
Estimated pi: 3.14...
Elapsed seconds: ...
```

The node name, point count, estimate, and elapsed time vary. A result near `3.14` means the calculation ran. You don't need accounting enabled, `sacct`, or a database for this first demo.

## Step 10: Explain it and clean up

Interview explanation:

> “I submitted one Python job using `sbatch`. Slurm placed it on one CPU in the HTC partition. I checked the queue with `squeue`, viewed the partition with `sinfo`, and read the job output. CycleCloud manages Azure cluster lifecycle; Slurm manages job scheduling.”

After the demo:

1. Check your jobs with `squeue -u "$USER"`. Cancel only your own demo job if it is still running: `scancel YOUR_JOB_ID`.
2. Terminate the Slurm cluster in CycleCloud.
3. If you want to stop charges for the whole experiment, delete the **dedicated** demo resource group in Azure portal only after verifying it contains no unrelated resources. This also removes the Workspace, network, storage, and Bastion.
4. Check Cost Management and the resource list afterward. Charges already accrued are not refunded.

Do not delete the Workspace if you plan to continue practicing.

## Official references

- [CycleCloud Workspace for Slurm overview](https://learn.microsoft.com/azure/cyclecloud/overview-ccws?view=cyclecloud-8)
- [Plan a CycleCloud Workspace for Slurm deployment](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/plan-your-deployment?view=cyclecloud-8)
- [Create an Entra app registration for CycleCloud](https://learn.microsoft.com/azure/cyclecloud/how-to/create-app-registration?view=cyclecloud-8)
- [Request Azure VM quota](https://learn.microsoft.com/azure/quotas/per-vm-quota-requests)
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
- [Connect to the CycleCloud portal through Bastion](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-portal-with-bastion?view=cyclecloud-8)
- [Connect to a Slurm login node through Bastion](https://learn.microsoft.com/azure/cyclecloud/how-to/ccws/connect-to-login-node-with-bastion?view=cyclecloud-8)

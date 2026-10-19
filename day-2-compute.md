# Day 2: Compute and Deployment

**Lenses:** 3 Compute · 6 Operations (build/deploy)
**Today's question:** *Where should this code run, and how does it get there?*

---

## Read (40 min)

### 2.1 The compute spectrum: one idea

```
 MORE CONTROL / MORE OPS WORK                                LESS CONTROL / LESS OPS WORK
 ◄──────────────────────────────────────────────────────────────────────────────────────►
 Compute Engine  →  Managed Instance  →  GKE Standard → GKE Autopilot → Cloud Run → Cloud Run
 (a VM)             Groups (VM fleet)    (you run       (Google runs    (container,  functions
                                          nodes)         nodes)          scales to 0) (a function)
 You manage: OS, patching, scaling ............................................ just your code
 Billing:    per VM-second .............. per node ...... per pod ...... per request / instance-second
```

**Default rule:** start at **Cloud Run**. Move left only when something forces you:

| Move left to… | …when you need |
|---|---|
| **GKE** | Many services with complex inter-service networking, Kubernetes ecosystem (Helm, operators, service mesh), stateful sets, GPUs with fine control, portability across clouds, or a platform team already running Kubernetes |
| **Compute Engine / MIG** | Lift-and-shift of existing VMs, OS-level control or licensing, non-containerized software, special hardware (very large memory, specific GPUs/TPUs), long-running stateful processes |
| **Cloud Run functions** (move right) | A small piece of glue code reacting to an event (file uploaded, message published) |
| **Batch / Cloud Run jobs** | Run-to-completion work rather than serving requests |

### 2.2 Cloud Run: the one to know well

- You give it a **container image** (or source code, and it builds the image). It gives you an **HTTPS URL**, autoscaling (including **to zero**), and TLS.
- **Service** = serves requests. **Job** = runs to completion (batch, migrations, cron with Cloud Scheduler).
- **Revision** = immutable snapshot of code + config. Every deploy creates one. **Traffic splitting** across revisions gives you canary and blue/green deployments for free.
- **Concurrency:** one instance handles up to N requests at once (default 80). That's why it's cheaper than one-request-per-instance functions.
- **Cold starts:** scaling from 0 adds latency. Set `--min-instances=1` for latency-sensitive services (you pay for it idling).
- **Billing modes:** *request-based* (CPU only while handling requests; the default) or *instance-based* (CPU always on; needed for background work after the response).
- **Stateless:** the local disk is in-memory and disappears. Keep state in Cloud Storage, a database or a cache.
- **Ingress:** `all` / `internal` / `internal-and-cloud-load-balancing`. **Auth:** public (`allUsers` → `roles/run.invoker`) or IAM-authenticated callers only.
- **Identity:** each service runs as a **service account**. Always set one explicitly (`--service-account`).
- Reaching private resources (a database on a private IP in a VPC): **Direct VPC egress** (or the older Serverless VPC Access connector).

### 2.3 Compute Engine essentials

- **Machine families:** E2 (cheap general-purpose), N2/N4 (balanced), C3/C4 (compute-optimized), M (memory-optimized), A/G (GPUs). Custom machine types let you choose vCPU and RAM exactly.
- **Images** (boot OS) → **disks** (Persistent Disk / Hyperdisk; zonal or regional) → **snapshots** (backups, global).
- **Startup scripts** in metadata bootstrap a VM. **Instance templates** + **Managed Instance Groups (MIGs)** give you a fleet with **autoscaling**, **autohealing** (health checks) and **rolling updates**. A *regional* MIG spreads VMs across zones.
- **Spot VMs:** much cheaper but can be reclaimed at any time. Good for fault-tolerant batch work.
- **Live migration:** Google moves running VMs during host maintenance without rebooting them.
- **SSH:** `gcloud compute ssh` handles keys for you. With OS Login, IAM roles control who can SSH.

### 2.4 GKE essentials (enough to talk about it)

- Kubernetes: **cluster** = **control plane** (managed by Google) + **nodes** (VMs) running **pods** (one or more containers). **Deployments** keep N pods running. **Services** give them a stable address. **Ingress/Gateway** exposes them through a Google load balancer.
- **Autopilot:** Google manages the nodes and you pay per pod resource requests. **The default choice.** **Standard:** you manage node pools; choose it for special hardware or tuning.
- **Workload Identity Federation for GKE:** maps a Kubernetes service account to a GCP IAM principal, so pods get GCP credentials without keys.
- Regional cluster = control plane and nodes spread across zones (high availability). Zonal cluster = cheaper, single zone.

### 2.5 From code to running: the delivery pipeline

```
 git push ─► Cloud Build ─► Artifact Registry ─► Cloud Deploy (optional) ─► Cloud Run / GKE
            (build, test)    (stores images)       (promote dev→staging→prod)
```

- `gcloud run deploy --source .` does all of this in one command: it uploads the source, Cloud Build builds it (using a Dockerfile if one is present, otherwise buildpacks), pushes the image to Artifact Registry and deploys a new revision.
- **Artifact Registry** replaced Container Registry. Image paths look like `REGION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG`.
- In real teams, a **Cloud Build trigger** on a git push (or GitHub Actions using Workload Identity Federation) runs the pipeline.

---

## Lab (80 min)

```bash
source ~/gcpweek.env && gcloud config set project "$PROJECT_ID"
cd ~/gcp-learning/lab/app && cat main.py      # read the app first: 4 routes, no credentials
```

### Core A: a VM the old-fashioned way (20 min)

```bash
# Firewall rule: allow port 80 to VMs tagged "http-server" (rules belong to the VPC; tags pick targets)
gcloud compute firewall-rules create allow-http --network=default \
  --allow=tcp:80 --target-tags=http-server --source-ranges=0.0.0.0/0

# A VM that installs nginx on boot (e2-micro is free-tier in us-central1/us-east1/us-west1)
gcloud compute instances create web-1 --zone="$ZONE" --machine-type=e2-micro \
  --image-family=debian-12 --image-project=debian-cloud --tags=http-server \
  --metadata=startup-script='#!/bin/bash
apt-get update && apt-get install -y nginx
echo "Hello from $(hostname) in $(curl -s -H Metadata-Flavor:Google http://metadata.google.internal/computeMetadata/v1/instance/zone | cut -d/ -f4)" > /var/www/html/index.html'

VM_IP=$(gcloud compute instances describe web-1 --zone="$ZONE" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
sleep 60; curl "http://$VM_IP"           # give the startup script about a minute

gcloud compute ssh web-1 --zone="$ZONE" --command="sudo systemctl status nginx --no-pager | head -5"
#   You had to: choose a size, an OS, open a firewall, wait for boot, and you now own patching. Remember that feeling.

gcloud compute instances delete web-1 --zone="$ZONE" --quiet
```

> If `--network=default` fails with "network not found", your project was created without a default VPC (an org policy can do this). Create one with `gcloud compute networks create default --subnet-mode=auto`.

### Core B: the same idea on Cloud Run (30 min)

```bash
# One command: source → Cloud Build → Artifact Registry → Cloud Run revision
gcloud run deploy notes-api --source=. --region="$REGION" \
  --service-account="$APP_SA" --allow-unauthenticated --max-instances=3
#   Say Y to creating the Artifact Registry repo. Takes 2–4 minutes the first time.

URL=$(gcloud run services describe notes-api --region="$REGION" --format='value(status.url)')
echo "export URL=$URL" >> ~/gcpweek.env
curl "$URL/"
```

If the build fails with a permission error, the build service account needs a role. Grant it, then re-run the deploy:

```bash
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" --role="roles/run.builder"
```

If `--allow-unauthenticated` is rejected by an org policy, deploy without it and call the service with your identity: `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" "$URL/"`.

Now look at what was created:

```bash
gcloud artifacts repositories list --location="$REGION"          # where the image went
gcloud builds list --limit=3                                      # the build that made it
gcloud run revisions list --service=notes-api --region="$REGION"  # revision #1
```

### Core C: canary deploy with traffic splitting (20 min)

```bash
# Deploy revision 2 with 0% traffic, tagged "v2" so it gets its own test URL
gcloud run deploy notes-api --source=. --region="$REGION" --service-account="$APP_SA" \
  --update-env-vars=GREETING="hello from v2" --no-traffic --tag=v2

gcloud run services describe notes-api --region="$REGION" --format='value(status.traffic)'
curl "$URL/"                                          # still v1 for everyone
curl "$(gcloud run services describe notes-api --region="$REGION" \
  --format='value(status.traffic[].url)' | tr ';' '\n' | grep v2---)/"   # v2 through its tag URL (also printed by the deploy)

gcloud run services update-traffic notes-api --region="$REGION" --to-tags=v2=50   # canary: 50/50
for i in $(seq 1 10); do curl -s "$URL/" | grep -o '"greeting":"[^"]*"'; done
gcloud run services update-traffic notes-api --region="$REGION" --to-latest       # promote
```

Rollback is the same command pointed at the old revision: `--to-revisions=REVISION_NAME=100`.

### Core D: see the logs (10 min)

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="notes-api"' \
  --limit=10 --freshness=1h --format='table(timestamp, httpRequest.status, httpRequest.requestUrl)'
```

Then in the Console go to Cloud Run → notes-api and look at the Metrics, Logs and Revisions tabs.

### Stretch: GKE Autopilot (30 min, then delete it; it costs money while running)

```bash
gcloud services enable container.googleapis.com
gcloud container clusters create-auto lab-gke --region="$REGION"    # about 5–10 min
kubectl create deployment hello --image=us-docker.pkg.dev/google-samples/containers/gke/hello-app:1.0
kubectl scale deployment hello --replicas=3
kubectl expose deployment hello --type=LoadBalancer --port=80 --target-port=8080
kubectl get pods,svc -w      # wait for EXTERNAL-IP, Ctrl+C, then curl it
gcloud container clusters delete lab-gke --region="$REGION" --quiet
```

Compare: how many concepts did GKE need (cluster, deployment, replicas, service, load balancer) against Cloud Run (one command)? That gap is the operational cost you pay for the flexibility.

---

## Recall (25 min)

**Draw:** the compute spectrum from memory, with one "choose this when…" note under each option. Then draw the source → Cloud Build → Artifact Registry → Cloud Run pipeline.

**Answer:**
1. A team wants to run a containerized REST API with spiky traffic and no ops staff. Where should it run, and why?
2. What is a Cloud Run revision, and how do you do a canary?
3. Name 3 reasons to choose GKE over Cloud Run.
4. Name 2 reasons to choose Compute Engine.
5. How does code running on Cloud Run authenticate to Firestore? (No keys!)
6. What are cold starts, and how do you reduce them?
7. Zonal MIG vs regional MIG?
8. What does `gcloud run deploy --source .` actually do, step by step?

<details><summary>Answers</summary>

1. Cloud Run: serverless, scales to zero, fast autoscaling for spikes, no infrastructure to run.
2. An immutable snapshot of code + config. Deploy with `--no-traffic --tag`, then `update-traffic` to shift a percentage.
3. Kubernetes ecosystem and tooling, complex multi-service or service-mesh setups, stateful workloads, fine GPU/node control, portability, an existing platform team. (Any 3.)
4. Lift-and-shift, OS control or licensing, non-containerizable software, special hardware.
5. Through the attached service account: ADC fetches tokens from the metadata server, and IAM roles on that service account authorize access.
6. Latency when a new instance starts (from zero, or while scaling). Use min instances, a smaller image and lazy initialization.
7. Zonal = all VMs in one zone. Regional = spread across zones in a region (survives a zone outage).
8. Upload source → Cloud Build builds an image (Dockerfile or buildpacks) → push to Artifact Registry → create a new Cloud Run revision → route traffic to it.
</details>

## Work tie-in

- Where do your team's workloads run? Find them: `gcloud run services list`, `gcloud container clusters list`, `gcloud compute instances list` (in a work project, read-only).
- If you build ADK agents: is the agent served from Cloud Run, GKE or Vertex AI Agent Engine? Which service account does it run as, and what roles does that service account have?
- Find your CI/CD: Cloud Build triggers? GitHub Actions? Where do images live?

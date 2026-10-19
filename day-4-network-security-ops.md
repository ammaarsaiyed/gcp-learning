# Day 4: Network, Security, Operations

**Lenses:** 2 Network · 7 Security · 6 Operations
**Today's question:** *How do bits flow safely, and how do I know what's happening?*

---

## Read (40 min)

### 4.1 VPC in one diagram

```
 VPC "prod-vpc"  (GLOBAL)                                                  Internet
 ├── subnet us-central1   10.10.0.0/20   (REGIONAL) ── VMs, GKE nodes          ▲
 ├── subnet europe-west2  10.20.0.0/20   (REGIONAL) ── VMs                     │ outbound only
 ├── firewall rules       (VPC-level, target by tag / service account)   Cloud NAT (regional, via Cloud Router)
 ├── routes               (default route to internet, subnet routes, BGP-learned)
 └── Private Google Access (per subnet): private VMs can reach Google APIs without public IPs
```

- **Auto-mode** VPC = one subnet per region, created for you (the `default` network). **Custom-mode** = you plan the CIDRs. **Use custom mode in production.**
- **Firewall rules** are stateful. There's an implied *deny all ingress* and *allow all egress*. Lower priority number wins. Targets are **network tags** or **service accounts** (service accounts are better: tags can be set by anyone who can edit the VM). Organizations add **hierarchical firewall policies** at the org or folder level.
- **No external IP + Cloud NAT** is the secure default for VMs. For admin access, use **IAP TCP forwarding** (SSH through Google's identity-aware proxy; no bastion, no public IP).
- **Connecting VPCs:**
  - **VPC Network Peering:** two VPCs talk privately. **Not transitive** (A↔B and B↔C does not give A↔C).
  - **Shared VPC:** one **host project** owns the network, and many **service projects** put resources in it. **This is the enterprise standard**: a central network team, with app teams in their own projects.
  - **Private Service Connect (PSC):** a private endpoint IP in your VPC for a Google service, or for someone else's service.
- **Hybrid connectivity** (on-prem or other clouds):

  | Option | How | When |
  |---|---|---|
  | **HA VPN** | IPsec over the internet, 99.99% SLA | Quick, cheap, up to a few Gbps |
  | **Partner Interconnect** | Through a service provider | Private, 50 Mbps–50 Gbps, not in a colocation facility |
  | **Dedicated Interconnect** | Your own physical 10/100 Gbps links | Large, steady traffic; in a colocation facility |
  | **Cross-Cloud Interconnect** | Dedicated link to AWS/Azure/OCI | Multicloud |

  Cloud Router speaks **BGP** to exchange routes dynamically over VPN and Interconnect.

### 4.2 Load balancing: the decision

```
Is the traffic HTTP(S)?
├─ YES → Application Load Balancer (L7: URL routing, TLS termination, Cloud CDN, Cloud Armor)
│        ├─ Users worldwide, one anycast IP ────────► Global external ALB
│        ├─ Must stay in one region (residency) ────► Regional external ALB
│        └─ Internal service-to-service ────────────► Internal ALB
└─ NO (TCP/UDP) → Network Load Balancer (L4)
         ├─ Need TLS offload / proxy, global ───────► Proxy NLB
         └─ Preserve client IP, raw UDP, highest perf ► Passthrough NLB (regional, external or internal)
```

- Backends are MIGs, NEGs (network endpoint groups), **serverless NEGs** (Cloud Run behind a load balancer) or GCS buckets (static sites).
- Put **Cloud Armor** (WAF, DDoS, IP allow/deny, rate limiting) and **Cloud CDN** on the external ALB.
- **Cloud DNS:** public zones (internet) and private zones (visible only inside chosen VPCs).

### 4.3 Security: defense in depth (the checklist)

| Layer | Controls |
|---|---|
| **Identity** | IAM least privilege, groups, a service account per workload, no keys (WIF), IAP for human access to apps and VMs, MFA |
| **Guardrails** | **Organization Policies** (allowed regions, no external IPs, no service account keys, domain-restricted sharing) |
| **Network** | Private IPs, firewall rules/policies, Cloud NAT, Private Google Access/PSC, **VPC Service Controls** (a perimeter around Google APIs that stops data exfiltration even with valid credentials) |
| **Edge** | Cloud Armor (WAF/DDoS) on the external ALB |
| **Data** | Encrypted at rest by default; **CMEK** with Cloud KMS when you must control keys; Sensitive Data Protection (find and mask PII); bucket retention locks |
| **Secrets** | **Secret Manager** (versioned, IAM per secret, audited). Never put secrets in env files, images or git |
| **Detect and audit** | **Cloud Audit Logs** (Admin Activity is always on and free; Data Access is off by default except for BigQuery), **Security Command Center** (misconfigurations, threats) |

### 4.4 Operations (observability)

- **Cloud Logging:** everything lands here (platform logs, your stdout/stderr, audit logs). The **Log Router** sends logs through **sinks** to log buckets (retention), BigQuery (analysis), Cloud Storage (archive) or Pub/Sub (SIEM). **Log-based metrics** turn log patterns into metrics.
- **Cloud Monitoring:** metrics (built-in and custom), dashboards, **alerting policies** → notification channels, **uptime checks**, **SLO monitoring**. Install the **Ops Agent** on VMs for OS-level metrics and logs.
- **Trace** (latency across services), **Profiler** (CPU and heap), **Error Reporting** (groups exceptions).
- **What to alert on** (SRE golden signals): **latency, traffic, errors, saturation**. Define an **SLI** (what you measure, for example the % of requests under 300 ms), an **SLO** (the target, for example 99.5%) and the **error budget** (100% − SLO). Alert on budget burn rate, not on every blip.

---

## Lab (80 min)

```bash
source ~/gcpweek.env && gcloud config set project "$PROJECT_ID"
gcloud services enable iap.googleapis.com secretmanager.googleapis.com
```

### Core A: a private network, step by step (35 min)

```bash
# 1. Custom VPC + one subnet with Private Google Access
gcloud compute networks create lab-vpc --subnet-mode=custom
gcloud compute networks subnets create lab-subnet --network=lab-vpc --region="$REGION" \
  --range=10.10.0.0/24 --enable-private-ip-google-access

# 2. Only allow SSH from Google's IAP range (35.235.240.0/20), nothing else inbound
gcloud compute firewall-rules create lab-allow-iap-ssh --network=lab-vpc \
  --allow=tcp:22 --source-ranges=35.235.240.0/20

# 3. A VM with NO external IP
gcloud compute instances create private-vm --zone="$ZONE" --machine-type=e2-micro \
  --subnet=lab-subnet --no-address --image-family=debian-12 --image-project=debian-cloud

# 4. SSH in through IAP (no public IP, no bastion, no VPN)
gcloud compute ssh private-vm --zone="$ZONE" --tunnel-through-iap --command='
  echo "--- internet:";            curl -s -m 5 -o /dev/null -w "%{http_code}\n" https://example.com || echo "BLOCKED (no route out)"
  echo "--- Google APIs (PGA):";   curl -s -m 5 -o /dev/null -w "%{http_code}\n" https://storage.googleapis.com || echo "BLOCKED"'
#   Expect: internet BLOCKED, Google APIs reachable (an HTTP code). That's Private Google Access.

# 5. Give the subnet outbound internet through Cloud NAT (needs a Cloud Router)
gcloud compute routers create lab-router --network=lab-vpc --region="$REGION"
gcloud compute routers nats create lab-nat --router=lab-router --region="$REGION" \
  --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges
sleep 30
gcloud compute ssh private-vm --zone="$ZONE" --tunnel-through-iap \
  --command='curl -s -m 5 -o /dev/null -w "internet: %{http_code}\n" https://example.com'
#   Expect 200: the VM can go OUT, but nothing can come IN. This is the standard secure VM setup.

# 6. Clean up the billable parts (NAT and the VM)
gcloud compute instances delete private-vm --zone="$ZONE" --quiet
gcloud compute routers nats delete lab-nat --router=lab-router --region="$REGION" --quiet
gcloud compute routers delete lab-router --region="$REGION" --quiet
```

### Core B: secrets done properly (20 min)

```bash
printf 'hello from Secret Manager' | gcloud secrets create greeting --data-file=-
gcloud secrets versions list greeting

# Resource-level IAM: the app may read THIS secret only
gcloud secrets add-iam-policy-binding greeting \
  --member="serviceAccount:$APP_SA" --role="roles/secretmanager.secretAccessor"

# GREETING is currently a plain env var (from Day 2). Remove it, then inject it from the secret
gcloud run services update notes-api --region="$REGION" --remove-env-vars=GREETING
gcloud run services update notes-api --region="$REGION" --update-secrets=GREETING=greeting:latest
curl -s "$URL/"          # greeting now comes from Secret Manager; the code didn't change
```

An env-var secret is read when the instance starts. To rotate it, add a version (`gcloud secrets versions add`) and deploy a new revision. In production, **pin a version number** rather than `latest`, so a rotation is a deliberate deploy.

### Core C: who did what, and alerting (25 min)

```bash
# Audit log: every admin action you've taken this week, with who and what
gcloud logging read "logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity\"" \
  --limit=15 --freshness=1d \
  --format='table(timestamp, protoPayload.authenticationInfo.principalEmail, protoPayload.methodName)'

# A log-based metric: count client and server errors on the API
gcloud logging metrics create notes_api_errors \
  --description="4xx/5xx responses from notes-api" \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="notes-api" AND httpRequest.status>=400'

# Generate some errors (empty notes return 400)
for i in $(seq 1 20); do curl -s -o /dev/null -X POST "$URL/notes" -H "Content-Type: application/json" -d '{}'; done
```

Then in the **Console**:
1. **Monitoring → Metrics explorer**: find `logging/user/notes_api_errors`. You should see the spike (it can take a couple of minutes).
2. **Monitoring → Alerting → Create policy** on that metric (above 5 in 5 minutes) → add your email as a notification channel.
3. **Monitoring → Uptime checks → Create**: HTTPS, host = your Cloud Run hostname, path `/`.
4. **Logging → Log Router**: see the `_Required` and `_Default` sinks. These are where your logs go by default.

### Stretch

- Put Cloud Run behind a **global external ALB** with a **serverless NEG** and attach a **Cloud Armor** policy that blocks your own IP. Follow the "Set up a global external Application Load Balancer with Cloud Run" guide. Delete the forwarding rule afterwards (load balancers bill hourly).
- Create a **log sink** that exports Cloud Run logs to a BigQuery dataset, then query them with SQL.
- Check the org policies on a work project (read-only): `gcloud org-policies list --project=WORK_PROJECT_ID`.

---

## Recall (25 min)

**Draw:** a VPC with 2 regional subnets, a private VM in each, Cloud NAT, IAP SSH, Private Google Access, and a global external ALB in front of a MIG. Label what's global and what's regional.

**Answer:**
1. Is a GCP VPC regional or global? What about subnets?
2. A VM has no external IP and needs to (a) call the Cloud Storage API and (b) download OS patches. What enables each?
3. How do admins SSH into private VMs without a bastion or VPN?
4. Peering vs Shared VPC: when do you use each? Is peering transitive?
5. Users are worldwide and the app is HTTP. Which load balancer? Where do the WAF and CDN go?
6. On-prem needs a 10 Gbps private, steady connection, and they're in a colocation facility. Which option?
7. What does VPC Service Controls protect against that IAM doesn't?
8. Which audit logs are always on? Which ones do you have to enable?
9. Define SLI, SLO and error budget, one line each.

<details><summary>Answers</summary>

1. The VPC is global. Subnets are regional.
2. (a) Private Google Access on the subnet. (b) Cloud NAT.
3. IAP TCP forwarding (`gcloud compute ssh --tunnel-through-iap`), with a firewall rule allowing 35.235.240.0/20.
4. Shared VPC: one organization, central network team, many projects. Peering: connecting separate VPCs or organizations. Peering is not transitive.
5. The global external Application Load Balancer, with Cloud Armor and Cloud CDN attached to it.
6. Dedicated Interconnect.
7. Data exfiltration by a principal *with* valid credentials (for example copying a bucket to a project outside the perimeter).
8. Admin Activity (and System Event) are always on. Data Access logs must be enabled (except for BigQuery).
9. SLI = the measured indicator (for example the % of successful requests). SLO = the target for the SLI (99.9%). Error budget = 100% − SLO, the amount of unreliability you're allowed.
</details>

## Work tie-in

- Find your network design: `gcloud compute networks list`, `gcloud compute networks subnets list`. Is it a Shared VPC (is there a separate host project)? How do you connect to on-prem (`gcloud compute vpn-tunnels list`, `gcloud compute interconnects attachments list`)?
- Which load balancer fronts your main app? `gcloud compute forwarding-rules list`.
- Where are the secrets? Are any still in env files or CI variables?
- Open a dashboard or alert your team relies on. What SLO, if any, does it represent?

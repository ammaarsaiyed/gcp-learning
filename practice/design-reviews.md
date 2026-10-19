# Design reviews: spot the flaws

You're on the architecture review board. Each proposal below has **real problems mixed with perfectly good choices**. Pick the problems, then compare with the reviewer's notes. This trains the skill reviewers use: seeing how pieces interact and where they break.

In the [practice app](../app/index.html#architect) you tick the issues you'd raise and submit. Format: `- [x]` = a real issue, `- [ ]` = fine as proposed. The text after `|` is the reviewer's explanation.

---

## Review: "Quick win" GenAI pilot for the complaints team
id: rev-genai-pilot
design: To move fast, the team built a complaint-summarisation tool. Complaint text (with customer names and account numbers) is sent to Gemini using an AI Studio API key stored in a Cloud Run environment variable. The Cloud Run service allows unauthenticated access so the team can share the link. Every prompt and response is written to a Cloud Storage bucket "for evaluation later". The service runs in europe-west2 and stores chat history in Firestore.
nodes:
- staff | Complaints team | fixed | 0,1
- run | Cloud Run (allUsers invoker) | compute | 1,1
- key | AI Studio API key (env var) | security | 1,0
- model | Gemini (AI Studio) | ai | 2,0
- logs | Bucket: all prompts + responses | data | 2,2
- fs | Firestore (chat history) | data | 2,1
edges:
- staff > run | public URL
- run > model | API key
- run > logs | full text
- run > fs | history
issues:
- [x] The service is public (allUsers), so anyone with the URL can submit and read complaint summaries | Use IAP with corporate identity. A Confidential customer-data tool must never be internet-open.
- [x] Customer data goes through AI Studio under developer terms with API-key auth | Use Gemini on Agent Platform: IAM, VPC-SC, regional processing, enterprise data governance.
- [x] The API key is a long-lived secret in an env var | With Agent Platform you use the service account (no key at all). Otherwise Secret Manager at minimum.
- [x] Full prompts with PII are kept indefinitely in a bucket with no stated access controls or retention | Minimise (redact with Sensitive Data Protection), restrict access, set retention, and cover it in the DPIA.
- [x] There's no DPIA, model risk inventory entry or evaluation plan | Customer data + an LLM influencing complaint handling needs a DPIA and model-risk tiering, and evaluation evidence before wider use.
- [ ] Cloud Run in europe-west2 | A sensible serverless choice in the UK region.
- [ ] Firestore for chat history | Fine as a store, as long as retention and access are designed.

## Review: Payments service "with HA"
id: rev-payments-ha
design: Payments API on Cloud Run (europe-west2) behind a global external Application Load Balancer and Cloud Armor. Writes go to a Cloud SQL primary in zone europe-west2-a (HA not enabled, to save cost). To scale reads, all GET requests, including the "payment status" check the app calls right after paying, go to a read replica. The mobile client retries any request that takes over 3 seconds. A Pub/Sub consumer sends confirmation SMS for each payment event. Memorystore caches product data.
nodes:
- app | Mobile app | fixed | 0,1
- lb | Global external ALB + Cloud Armor | network | 1,1
- run | Cloud Run (europe-west2) | compute | 2,1
- sql | Cloud SQL primary (zone a, no HA) | data | 3,0
- rep | Read replica | data | 3,2
- cache | Memorystore | data | 2,0
- ps | Pub/Sub | integration | 3,1
- sms | SMS sender | compute | 4,1
edges:
- app > lb | HTTPS (retry >3s)
- lb > run | backend
- run > sql | writes
- run > rep | all reads
- run > cache | product data
- run > ps | events
- ps > sms | push
issues:
- [x] Cloud SQL without HA is a single-zone point of failure for a payments service | Enable HA (regional standby). Multi-zone compute is wasted if the database is zonal.
- [x] Reading payment status from an async replica straight after writing returns stale results | Read your own writes from the primary (or route by consistency need). Replica lag confuses customers into retrying.
- [x] Client retries on POST without idempotency keys can create duplicate payments | Require idempotency keys stored transactionally with the payment.
- [x] The SMS consumer isn't stated to be idempotent, and Pub/Sub is at-least-once | Deduplicate on payment ID, or customers get repeated SMS messages.
- [x] No DR position for a region loss is described | State the impact tolerance and RTO/RPO, and add a cross-region replica and runbook (or justify why not).
- [ ] Cloud Run behind a global ALB with Cloud Armor | A strong, standard front-end pattern.
- [ ] Memorystore for product data | A sensible read cache for slowly changing data.

## Review: Self-service analytics platform
id: rev-analytics
design: Analysts are granted BigQuery Admin on the analytics project to "unblock them". A Composer DAG loads data nightly using a service account key stored as an Airflow variable. The main transactions table (12 TB) is unpartitioned, and dashboards run `SELECT *` with filters on date. Datasets were created in the EU multi-region, although the policy requires UK-only storage for this data. CDC from the core system uses Datastream, and Dataplex records lineage.
nodes:
- an | Analysts (BigQuery Admin) | fixed | 0,1
- bq | BigQuery (EU multi-region) | data | 2,1
- tbl | 12 TB unpartitioned table | data | 3,1
- comp | Composer (SA key in variable) | integration | 1,2
- ds | Datastream CDC | integration | 1,0
- plex | Dataplex lineage | ops | 3,0
- dash | Dashboards (SELECT *) | ops | 3,2
edges:
- an > bq | admin
- comp > bq | nightly load
- ds > bq | changes
- bq > tbl | contains
- plex > bq | lineage
- dash > tbl | full scans
issues:
- [x] BigQuery Admin for all analysts is far beyond least privilege | Grant dataset-level Data Viewer/User roles through groups, with policy tags for sensitive columns.
- [x] Service account key in an Airflow variable | Composer runs as its own attached service account, so no keys are needed. Enforce the no-keys org policy.
- [x] Unpartitioned 12 TB table with SELECT * dashboards means huge scan costs and slow queries | Partition by date, cluster by common filters, select only the needed columns, require partition filters.
- [x] EU multi-region breaks the UK-only residency requirement | Recreate the datasets in europe-west2 and enforce `gcp.resourceLocations`.
- [x] There's no perimeter or exfiltration control for a project full of customer data | VPC-SC around the analytics projects, plus Data Access logs.
- [ ] Datastream for CDC | The right low-impact way to capture core changes.
- [ ] Dataplex for lineage | Good governance practice.

## Review: Hybrid network design
id: rev-network
design: The cloud VPCs use 10.0.0.0/8, the same block as the on-prem estate, "because it's what we know". One Dedicated Interconnect connection links London to GCP, and the design claims a 99.99% SLA. Team VPCs are peered to a hub VPC, and teams expect to reach each other and on-prem through the hub. Production uses the auto-mode default network. Cloud NAT handles egress, a hierarchical firewall policy blocks SSH from the internet, and Cloud DNS forwards corp names to on-prem.
nodes:
- dc | On-prem (10.0.0.0/8) | fixed | 0,1
- ic | Single Interconnect | network | 1,1
- hub | Hub VPC | network | 2,1
- a | Team VPC A (peered) | network | 3,0
- b | Team VPC B (peered) | network | 3,2
- def | default auto-mode network (prod) | network | 2,2
- nat | Cloud NAT | network | 2,0
- dns | Cloud DNS forwarding | network | 1,0
edges:
- dc > ic | circuit
- ic > hub | VLAN
- hub > a | peering
- hub > b | peering
- hub > nat | egress
- dns > dc | forward
issues:
- [x] Cloud ranges overlap with on-prem 10.0.0.0/8, so routing between them breaks | Plan non-overlapping IPAM with the network team. Use Private NAT or PSC only where overlap truly can't be avoided.
- [x] A single Interconnect connection can't give 99.99% | 99.99% needs four connections across two metros (99.9% needs two in one metro), plus redundant Cloud Routers.
- [x] Peering isn't transitive, so A can't reach B or on-prem through the hub | Use Network Connectivity Center, Shared VPC, or appliances or VPN in the hub for transit.
- [x] The auto-mode default network in production | Use custom-mode VPCs with planned subnets, and delete or skip the default network.
- [ ] Cloud NAT for egress | Standard.
- [ ] Hierarchical firewall policy blocking SSH from the internet | Exactly the kind of non-negotiable rule to set centrally.
- [ ] Cloud DNS forwarding zones to on-prem | Correct hybrid DNS pattern.

## Review: Servicing agent v0.1
id: rev-agent
design: The agent runs on Cloud Run as a service account with Editor on the project "so tools work". Its main tool is a generic HTTP caller with the internal API catalogue in its prompt. It executes account actions as soon as the model decides to. It uses the model's "latest" alias to always get improvements. Model Armor screens user messages. Each step is traced to Cloud Trace. There's no limit on reasoning or tool loops.
nodes:
- cust | Customer | fixed | 0,1
- run | Agent on Cloud Run (SA = Editor) | compute | 1,1
- llm | Gemini (latest alias) | ai | 2,0
- http | Generic HTTP tool | compute | 2,2
- apis | Internal APIs | fixed | 3,2
- armor | Model Armor | security | 1,0
- trace | Cloud Trace | ops | 3,1
edges:
- cust > armor | message
- armor > run | screened
- run > llm | plan
- run > http | any call
- http > apis | anything reachable
- run > trace | spans
issues:
- [x] Editor on the project gives the agent (and any prompt injection) enormous blast radius | A dedicated, least-privilege identity per tool (MCP server or function), scoped to exact actions.
- [x] A generic HTTP tool lets the model call any reachable API | Narrow, schema-validated tools for approved actions only.
- [x] No human confirmation before account actions | Require explicit customer confirmation for consequential actions (Consumer Duty, safety).
- [x] The "latest" model alias changes behaviour without validation | Pin versions, evaluate upgrades, and record the version in model-risk documentation.
- [x] Unbounded loops risk runaway cost and repeated actions | Set step limits, timeouts and budgets per session.
- [x] Only user messages are screened, but tool and API responses can carry indirect injection | Screen and treat all tool output as untrusted.
- [ ] Tracing each step to Cloud Trace | Exactly right for audit and debugging.

## Review: Disaster recovery plan
id: rev-dr
design: Production runs in europe-west2. The DR plan: Terraform modules can recreate the stack in europe-west1. Cloud SQL has an async cross-region replica (RPO about 5 minutes, accepted by the business). Nightly database exports are stored in a bucket in europe-west2. Quotas in europe-west1 are at defaults. The public DNS record has a TTL of 24 hours. The plan has never been executed.
nodes:
- prim | Prod stack (europe-west2) | compute | 0,1
- sql | Cloud SQL primary | data | 1,1
- rep | Replica (europe-west1) | data | 2,1
- bk | Backups bucket (europe-west2) | data | 1,2
- tf | Terraform modules | ops | 2,0
- dr | DR stack (europe-west1, quotas default) | compute | 3,1
- dns | DNS (TTL 24h) | network | 0,0
edges:
- prim > sql | writes
- sql > rep | async
- sql > bk | nightly export
- tf > dr | recreate
- dns > prim | points to
issues:
- [x] Backups stored only in the primary region are lost with the region | Store backups cross-region (dual/multi-region bucket or a vault).
- [x] Default quotas in the DR region may block recreating production capacity | Pre-raise quotas (CPUs, IPs, GPUs) in the DR region and check them regularly.
- [x] A 24-hour DNS TTL means clients keep going to the dead region | Use a global load balancer (no DNS change needed) or a low TTL.
- [x] Never tested, so RTO is unknown | Run scheduled DR tests, measure the RTO, and fix what breaks (operational resilience requires testing).
- [ ] Async replica with RPO about 5 minutes | Acceptable, because the business explicitly accepted it.
- [ ] Terraform to recreate the stack | The right foundation for a pilot-light or warm DR.

## Review: Delivery pipeline
id: rev-cicd
design: GitHub Actions deploys using a service account JSON key stored as a repository secret. Developers can also run `gcloud run deploy` to production from their laptops for hotfixes. Images are tagged `:latest` and deployed by tag. The database password is baked into the image at build time. Images are stored in Artifact Registry. Cloud Deploy requires approval for prod, and releases use a canary.
nodes:
- gh | GitHub Actions (SA key secret) | compute | 0,1
- dev | Developer laptops | fixed | 0,2
- ar | Artifact Registry (:latest) | data | 1,1
- img | Image with DB password | security | 1,0
- cd | Cloud Deploy (approval, canary) | ops | 2,1
- prod | Cloud Run prod | compute | 3,1
edges:
- gh > ar | push :latest
- ar > cd | release
- cd > prod | canary
- dev > prod | direct deploy
- img > ar | contains secret
issues:
- [x] A service account key as a GitHub secret | Use Workload Identity Federation restricted to the repo and branch.
- [x] Direct production deploys from laptops bypass review, approvals and provenance | Remove the permission. Hotfixes go through the pipeline (fast path), with break-glass through PAM for emergencies.
- [x] Deploying by a mutable `:latest` tag | Deploy by digest, so what's tested is what runs.
- [x] Secrets baked into the image | Inject at runtime from Secret Manager. Anyone with image access can read baked-in secrets, and rotation needs a rebuild.
- [x] No Binary Authorization, so nothing stops unverified images running | Enforce attestations or provenance at admission.
- [ ] Artifact Registry for images | Correct.
- [ ] Cloud Deploy approvals and canary | Good practice.

## Review: Event-driven KYC intake
id: rev-kyc
design: Customers upload ID documents to a bucket with `allUsers` read access, so the review UI can show previews easily. A Pub/Sub push subscription posts events to a Cloud Run endpoint that allows unauthenticated requests. The subscription has no dead-letter topic. Workflows orchestrates Document AI extraction and a Gemini consistency check. The bucket has no retention or deletion policy.
nodes:
- cust | Customer | fixed | 0,1
- gcs | Bucket (allUsers read) | data | 1,1
- ps | Pub/Sub push (no DLQ) | integration | 2,1
- run | Cloud Run (unauthenticated) | compute | 3,1
- wf | Workflows | integration | 3,0
- dai | Document AI | ai | 4,0
- gem | Gemini check | ai | 4,1
edges:
- cust > gcs | upload
- gcs > ps | notification
- ps > run | push (no auth)
- run > wf | start
- wf > dai | extract
- wf > gem | verify
issues:
- [x] Public read on a bucket of identity documents | A severe breach risk. Use private buckets, and short-lived signed URLs for previews. Enforce public access prevention.
- [x] The push endpoint accepts unauthenticated requests, so anyone can forge events | Require OIDC authentication on push (a service account with invoker), and keep the service non-public.
- [x] No dead-letter topic: poison messages retry forever and failures go unnoticed | Add a DLT with max delivery attempts and alert on it.
- [x] No retention or deletion policy for sensitive documents | Define retention per the regulatory requirement, then delete (lifecycle rules). UK GDPR storage limitation.
- [ ] Workflows orchestrating extraction and checks | Good fit: retries, error handling, and room for human-review callbacks.
- [ ] Document AI for ID extraction | The right specialised tool.

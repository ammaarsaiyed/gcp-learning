# Day 5: Architecture (Design It, Break It Down)

**Lenses:** all 8
**Today's question:** *Given a problem, what do I build on GCP, and why?*

Today has a different shape: **30 min read → 90 min design drills → 30 min breaking down real diagrams → 15 min teardown → 15 min plan for next weeks.**

---

## Read (30 min)

### 5.1 The design method (use it every time)

```
1. REQUIREMENTS   Functional: what does it do?   Users: who, how many, where?
                  Non-functional: latency, availability (SLO), RTO/RPO, data residency, compliance, budget, team skills
2. LENSES         Walk the 8 lenses (solution-design-template.md) and pick a service per lens with the decision trees
3. NFR PASS       Check the design against the Well-Architected pillars:
                  operational excellence · security · reliability · cost · performance · sustainability
4. TRADE-OFFS     State what you gave up ("Cloud SQL over Spanner: cheaper, but single-region writes")
5. DIAGRAM        Boxes = services, arrows = data flow, labeled with protocol and identity
```

The **trade-offs** step is what separates a design from a shopping list. Every choice should have a "because" and a "given up".

### 5.2 Reliability vocabulary

- **RTO** (Recovery Time Objective): how long you can be down. **RPO** (Recovery Point Objective): how much data you can lose.
- **High availability** (survive a zone loss) = multi-zone: regional MIG, regional GKE, Cloud SQL HA, Cloud Run (already regional).
- **Disaster recovery** (survive a region loss), in increasing cost and decreasing RTO:

  | Pattern | What runs in region 2 | RTO / RPO | Example |
  |---|---|---|---|
  | Backup and restore (cold) | Nothing; backups in a multi-region GCS bucket | Hours / hours | Internal tools |
  | Warm standby | A scaled-down copy plus a DB replica | Minutes / minutes | Most business apps |
  | Hot (active-active) | Full capacity, global LB, multi-region DB (Spanner) | ~0 / ~0 | Payments, global consumer apps |

### 5.3 Six reference patterns (learn to draw these from memory)

**P1. Serverless web app / API** (the default for new apps)
```
Users ─► Cloud DNS ─► Global ext. ALB (+Cloud Armor, +Cloud CDN) ─┬─► backend bucket (static frontend in GCS)
                                                                   └─► serverless NEG ─► Cloud Run (API, own SA)
                                                                                           ├─► Firestore / Cloud SQL (private IP)
                                                                                           ├─► Secret Manager
                                                                                           └─► Pub/Sub ─► async workers
Auth: Identity Platform (customers) or IAP (employees) · Ops: Logging/Monitoring/Error Reporting · CI/CD: Cloud Build → Artifact Registry → Cloud Deploy
```

**P2. Classic 3-tier, highly available** (lift-and-shift or VM-bound software)
```
Users ─► Global ext. ALB ─► Regional MIG (web/app tier, across 3 zones, autoscaling, autohealing)
                               └─► Internal ALB ─► Regional MIG (app tier) ─► Cloud SQL HA (+ cross-region read replica for DR)
Private subnets, no external IPs, Cloud NAT for patches, IAP for SSH, Shared VPC from the network team
```

**P3. Event-driven processing**
```
Upload to GCS ─► Eventarc ─► Cloud Run (process) ─► results to GCS/Firestore
                                    └─► Pub/Sub "processed" ─► fan-out: notifier, indexer, BigQuery subscription
Dead-letter topics for failures, idempotent consumers, Cloud Scheduler for periodic sweeps
```

**P4. Analytics: streaming and batch**
```
Streaming: Apps/devices ─► Pub/Sub ─► Dataflow (streaming) ─┬─► BigQuery (analytics) ─► Looker
                                                            ├─► Bigtable (low-latency serving)
                                                            └─► GCS (raw archive, lifecycle → Archive)
Batch:     Sources ─► GCS (landing) ─► Dataflow/Dataproc or BigQuery SQL (ELT) ─► BigQuery
           DB CDC  ─► Datastream ─► BigQuery          Orchestration: Cloud Composer or Workflows + Scheduler
```

**P5. GenAI / agent application (RAG + tools)**
```
Users ─► IAP or Identity Platform ─► Frontend (Cloud Run)
              ─► Agent (ADK) on Agent Runtime or Cloud Run ─┬─► Gemini on Agent Platform (reasoning)
                                                                       ├─► Retrieval: vector search (AlloyDB pgvector /
                                                                       │    Vector Search / BigQuery vector search)       
                                                                       ├─► Tools: internal APIs (Cloud Run), BigQuery, A2A to other agents
                                                                       └─► Session/memory state (Agent Runtime sessions / Firestore)
Ingestion: docs in GCS ─► Eventarc ─► Cloud Run job (chunk, embed with Agent Platform embeddings) ─► vector store
Guardrails: service account per agent with least privilege on its tools, Secret Manager, VPC-SC around data, Cloud Trace for agent steps, evaluation datasets
```

**P6. Enterprise landing zone** (what your company's org probably looks like)
```
Organization ── Org Policies (locations, no SA keys, no external IPs) ── Hierarchical firewall policies
├── Folder: common   ── projects: logging (aggregated log sinks), security (SCC), network-hub (Shared VPC host, Interconnect/VPN)
├── Folder: prod     ── service projects attached to the prod Shared VPC
└── Folder: nonprod  ── service projects attached to the nonprod Shared VPC
Identity: Cloud Identity synced from the corporate IdP, groups → IAM roles at the folder level · All of it built with Terraform
```
Google publishes this as the **Enterprise foundations blueprint**. Skim its overview.

### 5.4 Infrastructure as code (read, don't run)

Everything you clicked or typed this week is normally Terraform. Day 3's Pub/Sub → BigQuery part looks like this:

```hcl
resource "google_pubsub_topic" "note_events" {
  name = "note-events"
}

resource "google_bigquery_dataset" "gcpweek" {
  dataset_id = "gcpweek"
  location   = "us-central1"
}

resource "google_bigquery_table" "notes_raw" {
  dataset_id = google_bigquery_dataset.gcpweek.dataset_id
  table_id   = "notes_raw"
  schema     = jsonencode([{ name = "data", type = "STRING" }])
}

resource "google_pubsub_subscription" "to_bq" {
  name  = "note-events-to-bq"
  topic = google_pubsub_topic.note_events.id
  bigquery_config {
    table = "${google_bigquery_table.notes_raw.project}.${google_bigquery_table.notes_raw.dataset_id}.${google_bigquery_table.notes_raw.table_id}"
  }
}

resource "google_pubsub_topic_iam_member" "app_can_publish" {
  topic  = google_pubsub_topic.note_events.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:notes-api-sa@my-project.iam.gserviceaccount.com"
}
```

Notice that the Terraform resources line up with the gcloud commands. If you can do it in gcloud, you can read the Terraform.

---

## Design drills (90 min)

For each drill: **15 minutes on paper** using [the template](cheatsheets/solution-design-template.md) → draw it → *then* open the model answer and diff it against yours. Many answers are valid. Check whether your **reasoning** covers the same lenses and trade-offs.

### Drill 1: Photo app startup
3 engineers. A mobile app where users upload photos; the app makes thumbnails and shows a feed. Unpredictable viral spikes. Users worldwide. Tiny budget until funding.

<details><summary>Model answer</summary>

- **Identity:** Identity Platform / Firebase Auth for end users. Separate service accounts for the API and the thumbnailer.
- **Network:** global external ALB + Cloud CDN for images and the frontend; Cloud Armor for basic DDoS and rate limiting.
- **Compute:** Cloud Run API (scales to zero, absorbs spikes). The thumbnailer is a Cloud Run function triggered by Eventarc on GCS object finalize.
- **Data:** GCS for originals and thumbnails (clients upload directly with **signed URLs**, so the API isn't in the data path). Firestore for metadata and the feed (serverless, real-time).
- **Integration:** Eventarc (upload event), Pub/Sub if more processors are added later (moderation, tagging).
- **Ops:** Cloud Logging/Monitoring, Error Reporting, uptime check, budget alerts.
- **Security:** private buckets + signed URLs, uniform bucket-level access, Secret Manager.
- **Cost:** everything scales to zero; lifecycle old originals to Nearline/Coldline; CDN cuts egress.
- **Trade-off:** Firestore over Cloud SQL means flexible schema and no server to run, but complex relational queries are harder.
</details>

### Drill 2: Migrate a 3-tier app in 3 months
A retailer runs a Java web app on 12 on-prem VMs with MySQL (2 TB). Must move in 3 months with minimal code changes. 99.9% availability. On-prem inventory systems stay on-prem for now.

<details><summary>Model answer</summary>

- **Approach:** rehost first, modernize later. Use Migrate to Virtual Machines for the VMs and Database Migration Service for MySQL → Cloud SQL.
- **Network:** Shared VPC (host project from the network team); **HA VPN** to start, Partner/Dedicated Interconnect if bandwidth needs grow; Cloud DNS private zones + DNS forwarding to on-prem.
- **Compute:** web and app tiers on **regional MIGs** (3 zones, autohealing) behind a **global external ALB** (web) and an internal ALB (app).
- **Data:** **Cloud SQL for MySQL HA** (regional, automatic failover) + a cross-region read replica for DR; private IP.
- **Security:** no external IPs, Cloud NAT, IAP for SSH, Cloud Armor on the ALB, secrets in Secret Manager.
- **Ops:** Ops Agent on VMs, dashboards, alerting on the golden signals, Cloud SQL backups + point-in-time recovery.
- **Reliability:** 99.9% → multi-zone is enough. DR = warm standby in a second region (replica promoted).
- **Phase 2:** containerize to GKE Autopilot or Cloud Run, maybe AlloyDB.
- **Trade-off:** rehosting is faster and lower-risk now, but costs more and keeps VM ops until phase 2.
</details>

### Drill 3: IoT telemetry
1M devices send a reading every 10s (~100k messages/s). Real-time anomaly alerts within seconds, per-device dashboards (last 24h, low latency), 5-year history for analysts.

<details><summary>Model answer</summary>

- **Ingest:** devices → an ingestion endpoint (Cloud Run or GKE; an MQTT broker on GKE if devices speak MQTT) → **Pub/Sub** (decouples and buffers). (Google retired IoT Core in 2023, so use partner or self-managed MQTT.)
- **Process:** **Dataflow streaming**: windowing, anomaly detection, enrichment.
- **Serve:** **Bigtable** for per-device time series (row key `deviceId#reversedTimestamp`), giving millisecond lookups for dashboards.
- **Analyze:** **BigQuery** (partitioned by day, clustered by deviceId) for 5-year analytics; Looker for dashboards.
- **Alert:** Dataflow publishes anomalies to a Pub/Sub `alerts` topic → Cloud Run notifier.
- **Archive:** raw data in GCS with lifecycle → Archive class (cheap 5-year retention).
- **Trade-off:** Bigtable has a cost floor (nodes) and needs careful row-key design, but nothing else gives this write rate with that read latency.
</details>

### Drill 4: Regulated analytics
A bank wants data scientists to analyze customer transactions. PII must not leave the EU. Analysts must not be able to export data outside the company, even with valid credentials. Full audit trail.

<details><summary>Model answer</summary>

- **Guardrails:** Org Policy `gcp.resourceLocations` = EU only; disable service account key creation.
- **Data:** BigQuery datasets in the EU multi-region; **CMEK** with Cloud KMS; **Sensitive Data Protection** to find and de-identify PII; **policy tags** (column-level security) and row-level security; authorized views for curated access.
- **Perimeter:** **VPC Service Controls** around the BigQuery/GCS projects, which blocks exfiltration to outside projects even with valid credentials.
- **Identity:** groups → predefined BigQuery roles at the dataset level; analysts use Agent Platform Workbench (formerly Vertex AI Workbench) inside the perimeter; IAP/BeyondCorp context-aware access (managed devices only).
- **Audit:** **Data Access audit logs** enabled, aggregated by a log sink into a locked logging project; Security Command Center.
- **Trade-off:** VPC-SC adds operational friction (perimeter bridges, ingress/egress rules), but it's the only control that addresses insider exfiltration.
</details>

### Drill 5: Internal AI assistant with agents
The company wants an assistant for employees that answers from internal docs (around 50k PDFs in Drive/GCS) and can take actions, like creating tickets in an internal API. Employees only. Answers must cite sources.

<details><summary>Model answer</summary>

- **Access:** frontend on Cloud Run behind **IAP** (Google identities, employees only).
- **Agent:** built with **ADK**, deployed on **Agent Runtime** (formerly Vertex AI Agent Engine; managed sessions, scaling) or Cloud Run (more control). **Gemini on Agent Platform** (formerly Vertex AI) as the model.
- **Retrieval (RAG):** ingestion pipeline: new doc in GCS → Eventarc → Cloud Run job parses and chunks → **Agent Platform embeddings** → vector store (**AlloyDB pgvector** if you also want SQL and filters, **Vector Search** for very large scale, BigQuery vector search for analytics-heavy cases). Store chunk → source URI so the answer can cite it. A managed alternative is Agent Search (formerly Vertex AI Search).
- **Tools:** the ticket API is a tool; the agent's **own service account** has only the role needed to call that API (Cloud Run invoker on that service). Other agents can be reached over A2A.
- **Security:** document-level ACLs enforced at retrieval time (filter by the user's groups), Secret Manager, VPC-SC around the data, and prompt-injection and response screening (for example Model Armor).
- **Ops:** Cloud Trace / Logging of agent steps and tool calls, an evaluation set of question → expected answer, token cost dashboards.
- **Trade-off:** Agent Runtime means less infrastructure to run, while Cloud Run gives you full control of the runtime and networking.
</details>

### Drill 6: Global game backend
A mobile game with players on every continent. Matchmaking needs low latency. Purchases must never double-charge. There are global leaderboards, and the business wants daily player analytics.

<details><summary>Model answer</summary>

- **Front door:** global external ALB (one anycast IP, nearest region) + Cloud Armor (DDoS).
- **Compute:** GKE Autopilot regional clusters in 3+ regions (multi-cluster Gateway), or Cloud Run in several regions behind the same ALB. Game servers that need UDP run on GKE (Agones) behind passthrough NLBs.
- **Data:** **Spanner multi-region** for accounts and purchases (globally strongly consistent, which prevents double-spending); **Memorystore** (Redis sorted sets) for leaderboards in each region, periodically reconciled.
- **Analytics:** game events → Pub/Sub → BigQuery subscription or Dataflow → BigQuery → Looker.
- **Trade-off:** Spanner is expensive, but its consistency is a hard requirement for money. Leaderboards tolerate eventual consistency, so they use a cheaper cache.
</details>

---

## Break down real architectures (30 min)

1. Open the **Google Cloud Architecture Center** (cloud.google.com/architecture) and pick 2 reference architectures: one close to your work, and one data or AI pattern.
2. For each diagram, **label every box with its lens (1–8)** and write one sentence on *why that service was chosen over its neighbor in the decision tree*.
3. Find what's **missing** from the diagram (it's usually ops, cost and identity). That's your critique.
4. Do the same for one real architecture diagram from your team.

---

## Teardown (15 min): don't skip it

```bash
source ~/gcpweek.env
gcloud projects delete "$PROJECT_ID"          # deletes EVERYTHING in the project (recoverable for 30 days)
gcloud billing budgets list --billing-account="$BILLING_ACCOUNT"   # optionally delete the budget too
rm ~/gcpweek.env
```

Deleting the whole project is the cleanest teardown. It's another reason to use one project per experiment.

---

## Final recall (the real test)

On a blank page, without notes:
1. Draw the **8 lenses** and put **at least 3 services** in each.
2. Draw the **compute spectrum** and the **storage decision tree**.
3. Draw **P1 (serverless web app)** and **P5 (agent app)** from memory.
4. Explain to an imaginary colleague, in 2 minutes each: IAM inheritance, why the VPC is global, Pub/Sub fan-out, and how Cloud Run authenticates to other services.

Whatever you couldn't reproduce becomes flashcards.

## Next 4 weeks (about 20 min a day)

| Week | Focus |
|---|---|
| 2 | Flashcards every day. Re-do the Day 3 lab from memory in a new project (no copy-paste). |
| 3 | Pick a work task and write a one-page design doc using the template before you start. |
| 4 | Go deep on your stack (for example GKE, Agent Runtime, BigQuery). Read its "best practices" docs page. |
| 5 | Open the ACE exam guide and tick what you can do. Go deeper only on the gaps that matter at work. |

# How to architect on GCP: putting the pieces together

The atlas teaches pieces. This guide teaches how to **combine** them: how to go from a vague request to a design you can defend, how one decision forces others, and what experienced reviewers check. Read it once properly, then use the [design lab](../app/index.html#architect) to practise it.

---

## 1. Why this is the hard part

Knowing that Cloud Run scales to zero and Spanner is strongly consistent is recall. Architecture is about **interactions**:

- Putting an LLM in the request path changes your **latency budget**, your **cost model**, your **failure modes** (429s), your **testing** (non-deterministic outputs) and your **governance** (model risk, data in prompts). One box, five consequences.
- Turning on VPC Service Controls breaks your **CI/CD**, your **log sinks**, any **SaaS** that reads your buckets and **on-prem** API access, until you design ingress and egress rules for each.
- Going multi-region changes your **database choice**, your **consistency model**, your **cost** (roughly double), your **data residency** position and your **DR testing** obligations.

So the skill is: **for every decision, ask "what does this force me to handle next?"**. Section 6 is a map of those knock-on effects.

---

## 2. The design loop

```
 1 UNDERSTAND   journeys, users, numbers, the business service it belongs to
 2 CONSTRAIN    regulation, data class, residency, existing estate, landing zone, skills, budget, deadline
 3 SHAPE        deployment archetype · interaction style · where state lives · trust boundaries
 4 DECIDE       walk the 8 lenses, start from defaults, deviate only for a stated reason
 5 STRESS-TEST  failure walk · threat model · scale ×10 · cost model · "what if the requirement changes?"
 6 COMMUNICATE  context diagram → container diagram → ADRs → review answers
        ↺ loop back whenever a stress test fails
```

Most bad designs skip step 1 (no numbers), step 2 (discover the residency rule in the review), or step 5 (never asked "what happens when the region goes?").

---

## 3. Step 1: Understand (turn vague requests into numbers)

### Functional: name 3–5 core journeys
"A customer views their balance", "a colleague asks a policy question", "a partner initiates a payment". Every box in your diagram must serve at least one journey. If a box doesn't, delete it.

### Non-functional: the questions that drive architecture

| Ask | Why it matters | Typical answers → design impact |
|---|---|---|
| **Who are the users, how many, where?** | Edge, auth, latency | Staff only → IAP. Customers in the UK → regional is fine. Global → global LB + CDN |
| **Peak requests per second? Growth?** | Scaling, DB choice | 50 rps → anything works. 50k rps writes → Spanner or Bigtable territory |
| **Latency target (p95/p99)?** | Sync vs async, caching, model choice | <100 ms → no LLM in path, cache features. Seconds → streaming LLM OK |
| **Availability target / impact tolerance?** | Zonal vs regional vs multi-region | 99.9% → multi-zone. Tolerance under 1 h for a region loss → second region |
| **RPO / RTO?** | Replication and backup design | RPO 0 cross-region → synchronous (Spanner). RPO minutes → async replica |
| **Data: volume, classification, residency?** | Storage, encryption, perimeter | Confidential + UK-only → CMEK, VPC-SC, `europe-west2`, careful with global AI endpoints |
| **Integrations: what does it call, what calls it?** | Network paths, auth, coupling | On-prem core banking → Interconnect + hybrid DNS. Partners → Apigee |
| **Consistency needs?** | DB, sync/async | Money → strong. Dashboards → eventual is fine |
| **Who operates it? Skills?** | Managed vs self-run | Small team → serverless. Platform team with K8s → GKE is reasonable |
| **Budget and deadline?** | Build vs buy, rehost vs refactor | 3 months → rehost or managed. Long horizon → refactor |
| **Which important business service does it support?** | Regulatory resilience | IBS → impact tolerance, mapping, testing evidence |
| **Is there a model making or influencing decisions?** | Model risk, explainability | Yes → SS1/23 inventory, validation, monitoring, human-in-the-loop |

### Back-of-the-envelope numbers (do these every time)

- **1 million requests per day ≈ 12 per second average**. Peaks are typically 3–10× average.
- 1 KB × 10 million records = 10 GB. 1 KB × 1 billion = 1 TB.
- **Latency:** same zone < 1 ms, cross-zone ≈ 1 ms, London ↔ Belgium ≈ 5–10 ms, London ↔ US East ≈ 70–80 ms. LLM calls: about 0.3–2 s to first token, several seconds for long outputs.
- **LLM cost sketch:** 50,000 questions per day × (3,000 input + 400 output tokens). Work out the input and output token totals per day, multiply by the per-token prices of the model you pick, then by 30. Doing this early prevents a "£40k/month surprise" and tells you whether caching, a smaller model or retrieval trimming matters.
- **Little's law:** concurrent requests = arrival rate × latency. 200 rps × 2 s LLM latency = 400 requests in flight. At a Cloud Run concurrency of 80, that's at least 5 instances, and that's before the model's quota becomes the bottleneck.

---

## 4. Step 2: Constrain (find the walls before you design)

In a bank, constraints usually decide more than technology preferences:

1. **Data classification** → required controls (encryption, location, perimeter, logging, AI usage rules).
2. **Residency and transfer rules** → regions allowed, global services to avoid, AI endpoint choice.
3. **The landing zone you must live in** → Shared VPC, org policies (no external IPs, no SA keys, CMEK required), approved services list, network egress patterns. **Design inside it, not around it.**
4. **Existing estate** → systems of record on-prem (latency, CDC, API wrappers), existing IdP, existing monitoring and SIEM.
5. **Third-party and outsourcing status** → SaaS or AI vendors trigger assessments that take time.
6. **People and time** → what the team can run at 3 a.m.

Write these down as the first slide of your design. Reviewers relax when they see you found the walls first.

---

## 5. Step 3: Shape (four big choices before any product names)

### 5a. Deployment archetype (Google's term)
| Archetype | Survives | Typical use | Cost and complexity |
|---|---|---|---|
| **Zonal** | Nothing above an instance failure | Dev, batch, tolerant internal tools | Lowest |
| **Regional** (multi-zone) | Zone loss | **Most production workloads**, 99.9–99.99% | Moderate |
| **Multi-regional** (active-passive or active-active) | Region loss | Important business services with tight impact tolerances | High (consistency, cost, testing) |
| **Global** | Region loss, serving worldwide | Consumer apps worldwide | High |
| **Hybrid** | Depends | Core systems on-prem, new capabilities in cloud | Network and DNS complexity |
| **Multicloud** | Provider-level issues (in theory) | Specific needs, concentration risk | Highest: lowest-common-denominator risk |

**Default for a UK bank workload:** regional in `europe-west2`, multi-zone, with a DR posture (backup/restore or warm standby) sized to the impact tolerance. Go active-active only when the tolerance demands it.

### 5b. Interaction style
- **Synchronous** where the user waits for the answer (queries, validations).
- **Asynchronous** (Pub/Sub, Tasks, Workflows) for side effects, fan-out, slow work and protecting fragile systems.
- Rule: **keep the synchronous path short.** Every hop adds latency and multiplies the failure probability.

### 5c. Where state lives (and who owns it)
- One owner per piece of data (a service or domain). Others get it through APIs, events or replicated read models. Never through shared database access.
- Decide the **system of record** vs **copies** (caches, analytics, search indexes, vector stores). Copies need a refresh strategy and their own retention and access rules (a vector index of confidential documents is itself confidential).

### 5d. Trust boundaries
Draw dashed lines where trust changes: internet ↔ edge, user ↔ service, service ↔ service, your projects ↔ Google APIs (perimeter), your org ↔ third parties and model providers, **user prompt ↔ LLM ↔ tools**. Every arrow that crosses a dashed line needs **authentication, authorization, encryption and logging**. That one rule produces most of a good security design.

### 5e. Planes: data, control and management
- **Data plane:** the actual traffic (requests, messages, queries).
- **Control plane:** configuration and orchestration (the Kubernetes API, Cloud Run deploys, IAM changes, routes).
- **Management plane:** how humans and pipelines change things (console, Terraform, CI/CD).
Design them separately: the data plane must keep running when the control plane is impaired (for example, existing Cloud Run instances keep serving even if you can't deploy). The management plane is where privilege lives, so lock it down hardest (PAM, pipelines only, break-glass).

---

## 6. Step 4: Decide, and the knock-on map

### 6a. Start from defaults. Deviate only with a reason.

| Lens | Bank-sensible default | Deviate when… |
|---|---|---|
| Identity | Corporate IdP → Cloud Identity / Workforce Federation; groups; a service account per workload; no keys; IAP for staff apps; PAM for prod | Customer-facing (CIAM / existing bank auth), partner (Apigee OAuth/FAPI) |
| Network | Shared VPC (from the platform team), private IPs only, PSC to Google APIs and managed services, Cloud NAT or Secure Web Proxy for egress, Interconnect to on-prem | Internet-facing → external ALB + Cloud Armor. Partners → mTLS |
| Compute | **Cloud Run** | K8s ecosystem or special hardware → GKE Autopilot. Lift-and-shift or licensing → GCE MIGs. Batch → Cloud Run jobs or Batch |
| Data (OLTP) | **Cloud SQL (Postgres)**, or **AlloyDB** for heavier work or vectors | Global or horizontal writes, 99.999% → Spanner. Massive key/time-series → Bigtable. Documents and mobile sync → Firestore |
| Data (analytics) | **BigQuery** with CDC (Datastream) and Dataform | Existing Spark → Dataproc. Complex streaming → Dataflow |
| Integration | **Pub/Sub** for events, **Cloud Tasks** to protect fragile targets, **Workflows** for multi-step processes, **Apigee** for APIs exposed beyond the team | Kafka skills or ecosystem → Managed Kafka |
| AI | Gemini on Agent Platform behind a gateway; RAG over AlloyDB or Agent Search; ADK on Cloud Run or Agent Runtime; Model Armor; evaluation in CI | Narrow tasks → pre-built APIs or classic ML. Self-hosting → GKE with GPUs |
| Ops | Cloud Logging + Monitoring, SLOs with burn-rate alerts, OpenTelemetry traces, Terraform via pipeline, Cloud Deploy | Existing enterprise tools (Splunk, Datadog): integrate, don't duplicate |
| Security | Org policies from the landing zone, CMEK on sensitive stores, VPC-SC around data and AI projects, Secret Manager, Binary Authorization, SCC | Highest sovereignty → EKM with Key Access Justifications |
| Cost | Labels, budgets, scale to zero for non-prod, CUDs for steady baselines | Large steady AI traffic → Provisioned Throughput |

### 6b. The knock-on map: "if you choose X, you must now handle Y"

This is the heart of integration. Learn these pairings.

| If you choose… | …you must now also handle |
|---|---|
| **Cloud Run** | Egress into the VPC (Direct VPC egress) for private databases and on-prem · DB connection limits as instances scale (pooling, max instances) · cold starts (min instances) · no local state (sessions elsewhere) · service identity and invoker IAM · request timeouts for long LLM calls |
| **GKE** | Upgrades and release channels · Pod IP planning · Workload Identity · network policies · who runs the platform · cost of idle nodes (or Autopilot) |
| **Serverless anything + on-prem dependency** | Private connectivity, hybrid DNS, the on-prem system's capacity (protect it with Cloud Tasks or rate limits), timeouts |
| **Pub/Sub / async** | Idempotent consumers (at-least-once) · ordering keys if needed · dead-letter topics + alerting · tracing across async hops (propagate trace context in attributes) · UX for "processing…" states · message storage policy for residency |
| **A cache (Memorystore)** | Invalidation strategy · stampede protection · what happens when the cache is down (it must be optional) · stale-data tolerance per use case |
| **Read replicas** | Replica lag → read-your-writes problems · routing logic · promotion runbook for DR |
| **Multi-region active-active** | A strongly consistent multi-region DB (Spanner) or conflict resolution · idempotency keys for retried writes · global LB health-based failover · residency approval for the second region · 2× cost · regular failover testing |
| **Active-passive DR** | Replication (async: accept RPO > 0) · IaC that can rebuild the stack · quotas pre-raised in the DR region · DNS/LB failover steps · runbook rehearsals · data in DR covered by the same controls |
| **CMEK** | The key becomes an availability dependency (KMS region = resource region) · key rotation · who can disable it (separation of duties) · service agents need key access · break-glass if a key is disabled by mistake |
| **EKM** | An external key manager's availability and latency are now on your critical path · its own DR |
| **VPC Service Controls** | Ingress/egress rules for CI/CD, log sinks, Cloud Build, third parties, on-prem (access levels) · `restricted.googleapis.com` DNS · dry-run first · developer friction · a perimeter design per data classification |
| **No external IPs (org policy)** | Cloud NAT or Secure Web Proxy for egress · IAP for admin access · private build pools · artifact proxies for packages |
| **Apigee** | Northbound networking (LB + PSC) · southbound reachability to backends · the OAuth model · rate-limit tiers · who owns API products · added latency hop · its availability in DR |
| **An LLM in the request path** | A latency budget with streaming · 429/quota handling and fallbacks · cost per request · prompt and data governance (PII redaction, logging) · evaluation sets in CI · model version pinning and re-validation · prompt injection containment · model risk inventory |
| **Agents with tools** | Least-privilege identity per tool · human confirmation for consequential actions · trajectory tracing · tool input validation · MCP server allow-listing · cost loops (step limits) · audit trail of actions |
| **RAG** | An ingestion pipeline (triggering, parsing, chunking, re-indexing) · ACL enforcement at retrieval time · index freshness · retrieval evaluation · the index's own classification, retention and residency |
| **BigQuery for analytics on customer data** | Dataset-level IAM design · policy tags and masking · partitioning and cost controls · Data Access logs · DLP scanning · retention · VPC-SC |
| **Microservices** | Service discovery, mTLS (mesh), distributed tracing, contract testing, per-service data ownership, versioning, many pipelines |
| **Third-party SaaS / model provider** | Outsourcing assessment · data transfer review · exit plan · their SLA in your impact-tolerance maths · private connectivity (PSC) if available |

### 6c. Common tensions (there's rarely a free lunch)

| Tension | Usual resolution |
|---|---|
| Consistency ↔ latency and availability (across regions) | Strong where money or state truly needs it (Spanner). Eventual elsewhere (caches, analytics) |
| Security ↔ developer velocity | Paved roads: the platform provides secure defaults (templates, pipelines, perimeters) so teams don't fight controls |
| Resilience ↔ cost | Size resilience to the business service's impact tolerance, not to "max everything" |
| Portability ↔ managed-service value | Portable where exit risk is high (containers, Postgres, open formats). Managed where value is high (BigQuery, Spanner) with a documented exit plan |
| Model capability ↔ cost and latency | Route: a small, fast model by default, a large model for hard cases. Cache and retrieve instead of huge prompts |
| Autonomy (agents) ↔ control | Workflow-style agents for regulated paths, autonomy only where errors are cheap and reversible |
| Observability ↔ data minimisation | Log structure, IDs and decisions. Redact or avoid raw PII and prompts, or store them in a restricted, short-retention store |

---

## 7. Step 5: Stress-test (the failure walk)

Walk your diagram against each line. Write down what happens and what limits the damage.

| Scenario | What to check |
|---|---|
| **A zone fails** | Are all tiers multi-zone? (Zonal VMs or disks? A zonal GKE cluster? A Memorystore without a replica?) |
| **The region fails** | RTO/RPO met? Data replicated? IaC ready? Quotas in DR? DNS/LB failover? Who decides to fail over, and how fast? |
| **A dependency is slow** (core banking, an LLM provider, a partner API) | Timeouts set? Retries bounded with jitter? Circuit breaker? Queue to absorb it? Graceful degradation path? |
| **Traffic ×10** (payday, an incident, a viral moment) | Autoscaling limits, DB connections, downstream rate limits, model quota, cost |
| **A bad deploy** | Canary? Automatic rollback on SLO burn? Database migration backwards-compatible? |
| **Data corruption or accidental deletion** | Point-in-time recovery? Immutable backups (vaults)? Bucket soft delete or versioning? Time travel in BigQuery? |
| **Leaked credentials** | No long-lived keys? Blast radius of each service account? Perimeter blocks use from outside? Detection in SCC or the SIEM? |
| **A malicious insider** | Separation of duties, PAM, VPC-SC, Data Access logs, alerts on bulk export |
| **Prompt injection through a document or email** | What tools can the agent call? Confirmation steps? Output filters? |
| **The provider exits or is unavailable for a long time** | Exit plan, data export paths, portable components, alternative model provider behind the gateway |
| **A regulator asks "show me"** | Can you produce lineage, access logs, model validation evidence, DR test results, change history? |

If any row gets the answer "the whole service is down and we'd find out from customers", go back to step 4.

---

## 8. Step 6: Communicate

### Diagrams that work (the C4 idea, simplified)
1. **Context diagram:** your system as one box, with users and external systems around it. Answers "what is this and what does it touch?".
2. **Container diagram:** the deployable and data pieces (Cloud Run services, databases, topics, gateways), with **labelled arrows** (protocol + identity + sync/async), **trust boundaries** dashed, **regions and zones** shown, and **classification** marked on data stores.
3. **Sequence views** for the 2–3 critical journeys (what calls what, in order). The [journeys](02-end-to-end-journeys.md) show how.

### Architecture decision records (ADRs)
One short page per significant choice: *context → options → decision → consequences*. "We chose AlloyDB over Spanner because the write volume is regional and modest. Consequence: region-level DR relies on a cross-region secondary with async replication (RPO ≈ seconds), which fits the 4-hour impact tolerance."

### The questions a bank architecture review board will ask (prepare answers)
1. Which business service does this support, and what's its impact tolerance? How does the design meet it, and how was it tested?
2. What data does it hold or process? What classification? Where is it stored and processed (including AI endpoints, logs, backups, indexes)?
3. Who and what can access the data? Human access path? Privileged access? How is access reviewed?
4. How is data protected at rest, in transit and in use? Who controls the keys?
5. What crosses the perimeter, and why? What's the egress story?
6. What are the third parties? Have outsourcing and DPIA assessments been done? What's the exit plan?
7. How is it deployed? Who can change production? What's the rollback?
8. How do you know it's healthy? SLOs? Who gets paged?
9. What happens when X fails? (Expect them to pick your weakest dependency.)
10. Is there a model? Is it in the inventory, tiered, validated, monitored? What's the human oversight?
11. What does it cost now and at 10× scale? Who owns the budget?
12. What's non-standard versus the platform's paved road, and why?

---

## 9. Anti-patterns to recognise instantly

- **Shared database between services:** couples deployments and ownership. Use APIs or events.
- **Synchronous chains of 5+ services** for one user request: latency and availability collapse.
- **"HA" that's all in one zone,** or a regional database with zonal compute.
- **Replication called backup:** corruption replicates too.
- **Default service accounts with Editor,** or one service account shared by many workloads.
- **Service account keys in CI variables:** use Workload Identity Federation.
- **Public IPs "temporarily" on VMs:** use IAP, NAT or a proxy.
- **Secrets in env files, images or Terraform state in git.**
- **Unbounded retries** at every layer: retry storms during incidents.
- **An LLM doing arithmetic or policy lookups from memory:** use tools and retrieval.
- **An agent with broad tools and no confirmation step.**
- **Logging full prompts with customer PII forever** in a widely readable bucket.
- **Multi-region "because resilience"** without an impact-tolerance reason, and never tested.
- **Building on a service the landing zone doesn't allow,** discovered at review time.
- **No numbers anywhere** in the design.

---

## 10. A 60-second mental checklist (memorise this)

> **Who** uses it and **how many** → **what data**, how sensitive, **where** → **which path** do requests take (draw it) → **where does state live** → **what's async** → **who/what can access what** (identities, perimeter) → **what happens when each box fails** → **how do we deploy, observe and roll back** → **what does it cost** → **which regulation does it touch**.

If you can answer those ten for any system, you can design it and you can review someone else's.

Next: [End-to-end journeys](02-end-to-end-journeys.md) show these ideas working together across real architectures.

# 09 · Reliability, operations and delivery

Keeping systems up, knowing when they aren't, and changing them safely. In a UK bank this domain maps directly onto operational resilience regulation (see file 12).

---

### Availability and "the nines"
`core` · Related: SLI/SLO/SLA, High availability
**What:** Availability = the proportion of time (or of requests) a service works. Downtime budgets: **99%** ≈ 7.3 h/month · **99.9%** ≈ 43.8 min/month · **99.95%** ≈ 21.9 min/month · **99.99%** ≈ 4.4 min/month · **99.999%** ≈ 26 s/month.
**How:** Serial dependencies multiply: a service that needs A (99.95%) *and* B (99.95%) is at most about 99.9%. Redundancy improves availability: two independent 99% replicas, where either can serve, give about 99.99%.
**Watch out:** Each extra nine costs roughly an order of magnitude more effort. Choose the target from business impact, and set it in line with the *impact tolerance* for that business service.

### SLI, SLO, SLA and error budgets
`core` · Related: Availability, Alerting, Burn rate
**What:** **SLI** (indicator): a measured ratio of good events to total events, for example the proportion of requests that return 2xx within 300 ms. **SLO** (objective): the internal target for an SLI over a window, for example 99.9% over 28 days. **SLA** (agreement): a contractual promise with penalties, set looser than the SLO. **Error budget:** 100% − SLO, the amount of unreliability you're allowed to "spend" on releases, experiments and incidents.
**How:** An **error budget policy** says what happens when the budget is used up: freeze features and focus on reliability. That's what makes SLOs drive decisions rather than sit on dashboards.
**GCP:** Cloud Monitoring **SLO monitoring** (request-based or windows-based SLIs on Cloud Run, GKE, load balancers, Cloud Service Mesh or custom metrics) with burn-rate alerts. Google publishes SLAs per product (for example Cloud Run 99.95%, Spanner multi-region 99.999%). Your SLO can't be higher than your dependencies allow.

### Burn rate alerting
`working` · Related: SLI/SLO/SLA, Alerting
**What:** Alerting on *how fast* you're consuming the error budget instead of on raw thresholds. A burn rate of 1 uses exactly the budget over the window. 14.4× over 1 hour means 2% of a 30-day budget gone in an hour, which should page someone.
**How:** Use multi-window, multi-burn-rate alerts (a fast window for sudden outages, a slow one for gradual degradation). This gives high precision (few false pages) and good recall.

### High availability vs disaster recovery
`core` · Related: RTO and RPO, Failure domains, Replication
**What:** **High availability (HA):** survive *component and zone* failures automatically with little or no disruption (redundancy within a region). **Disaster recovery (DR):** recover from *large-scale* events (region loss, data corruption, ransomware, a cyber attack) to a defined RTO and RPO, often involving a failover decision.
**Watch out:** Replication isn't backup. Corruption and deletion replicate instantly. DR needs immutable, point-in-time copies as well.

### RTO and RPO
`core` · Related: High availability vs disaster recovery, Backup and PITR, Impact tolerance
**What:** **RTO** (Recovery Time Objective): the maximum acceptable time to restore service. **RPO** (Recovery Point Objective): the maximum acceptable data loss, measured as time (for example "the last 5 minutes of transactions").
**How:** RPO drives the replication and backup design (synchronous → RPO ≈ 0; async → seconds to minutes; nightly backup → up to 24 h). RTO drives the standby design (hot, warm, cold) and the level of automation.

### DR patterns: backup/restore, pilot light, warm standby, active-active
`core` · Related: RTO and RPO, Multi-region
**What:** **Backup and restore (cold):** only backups in another region; rebuild on disaster (RTO hours or days, cheapest). **Pilot light:** core data replicated and minimal infrastructure defined (often as code), scaled up on failover. **Warm standby:** a scaled-down but running copy in region 2, with replicated databases (RTO minutes). **Hot / active-active:** full capacity in multiple regions serving traffic simultaneously (global load balancing + multi-region databases; RTO ≈ 0; most expensive and complex).
**GCP:** IaC (Terraform) + cross-region Cloud SQL or AlloyDB replicas + a dual- or multi-region GCS bucket + Artifact Registry in multiple regions + a global load balancer gives a typical warm standby. Spanner multi-region + global load balancing + Cloud Run in two or more regions gives active-active. Rehearse it: a DR plan that hasn't been tested doesn't count.

### Failure domains: zones and regions
`core` · Related: Location scope, High availability
**What:** A **failure domain** is a set of resources that can fail together. In GCP, a **zone** is a failure domain within a region (independent power, cooling and networking). A **region** is a geographic area of three or more zones.
**How:** Zonal resources (VMs, zonal disks) need multi-zone redundancy for HA. Regional resources (regional MIGs, Cloud Run, Cloud SQL HA, regional Spanner) handle zone failure for you. Multi-region resources handle region failure. Check each product's documented failure behaviour.
**GCP:** London is `europe-west2` (3 zones), and it's currently Google Cloud's only UK region. UK banks therefore usually get HA from multiple London zones. For region-level DR they pair it with another region (often `europe-west1`, Belgium) where data policy allows data to leave the UK, or with on-prem. Check current region availability and your bank's residency policy.

### Redundancy and N+1 capacity
`working` · Related: Failure domains, Capacity planning
**What:** Provisioning enough spare capacity that losing one unit (an instance, a zone) still leaves enough to serve peak load. With 3 zones, each zone must handle 50% of peak if one fails (N+1 across zones). For maintenance during an outage you need N+2.

### Graceful degradation
`working` · Related: Circuit breaker, Load shedding
**What:** Keeping core functions working when parts fail: serve cached balances if the live ledger is slow, disable recommendations rather than the whole app, fall back to a smaller model or a "please try later" response when the LLM provider returns 429s.

### Observability vs monitoring
`core` · Related: Cloud Logging, Cloud Monitoring, Distributed tracing
**What:** **Monitoring** watches known signals and alerts on known failure modes (dashboards, thresholds). **Observability** is the ability to understand *new, unexpected* behaviour from the telemetry the system emits: **logs** (discrete events), **metrics** (numeric time series), **traces** (request paths across services), plus **profiles**.
**GCP:** **Google Cloud Observability**: Cloud Logging, Cloud Monitoring, Cloud Trace, Cloud Profiler, Error Reporting, Managed Service for Prometheus. All of it is OpenTelemetry-friendly.

### Cloud Logging
`core` · Related: Cloud Audit Logs, Log sinks, Structured logging
**What:** Collects, stores, searches and routes logs from GCP services, your apps (stdout/stderr on Cloud Run and GKE, the Ops Agent on VMs) and audit logs.
**How:** The **Log Router** checks every entry against **sinks** (include and exclusion filters) → destinations: **log buckets** (with configurable retention and region, CMEK, and optional **Log Analytics** for SQL queries), BigQuery, Cloud Storage, Pub/Sub, or other projects. The `_Required` bucket (audit and admin logs, 400 days, unchangeable) and the `_Default` bucket (30 days, configurable) exist in every project. Query with the **Logging query language** in Logs Explorer. **Log-based metrics** turn matching entries into counters or distributions.
**Watch out:** Log volume is a real cost. Use exclusion filters, sampling and sensible log levels. Logs can contain PII, so redact before logging, and restrict log views.

### Structured logging and log correlation
`working` · Related: Cloud Logging, Distributed tracing
**What:** Writing logs as **JSON** with fields (severity, message, request ID, user ID, `logging.googleapis.com/trace`) instead of free text, so they're queryable and correlated.
**GCP:** On Cloud Run and GKE, JSON lines on stdout are parsed automatically. Include the trace ID so the Logs Explorer can show every log line for one request alongside its trace.

### Cloud Monitoring
`core` · Related: SLI/SLO/SLA, Alerting, Golden signals
**What:** Metrics, dashboards and alerting for GCP, hybrid and multicloud resources.
**How:** **Built-in metrics** for every service (no setup), **custom metrics** (OpenTelemetry, Prometheus, the API), **log-based metrics**, **Metrics Explorer**, **PromQL** querying, **dashboards** (including multi-project with metrics scopes), **alerting policies** (metric thresholds, absence, log-match, SLO burn-rate) → **notification channels** (email, SMS, Slack, PagerDuty, webhooks, Pub/Sub), **uptime checks** and **synthetic monitors** (scripted probes of user journeys), **Personalized Service Health** (Google-side incidents affecting your projects).
**GCP:** A **metrics scope** lets one project view metrics from many, which is how a central SRE or SOC team sees the whole estate.

### Distributed tracing
`core` · Related: OpenTelemetry, Structured logging, Agents
**What:** Following one request across services. A **trace** is a tree of **spans** (timed operations with attributes). **Context propagation** passes the trace ID and span ID in headers (W3C `traceparent`) from hop to hop.
**How:** The waterfall view shows where latency goes ("80% of this request was the LLM call; 15% was vector search").
**GCP:** **Cloud Trace** (with OpenTelemetry), with automatic spans for load balancers, Cloud Run and many client libraries. **For agents, tracing is essential**: each model call, tool call and retrieval should be a span. ADK and Agent Runtime emit traces.

### OpenTelemetry
`working` · Related: Distributed tracing, Cloud Monitoring
**What:** The vendor-neutral CNCF standard and SDKs for generating and exporting traces, metrics and logs (with semantic conventions, now including GenAI conventions for model calls and token usage), plus the **OpenTelemetry Collector** for processing and routing.
**GCP:** Google Cloud Observability ingests OTLP natively. Instrumenting once with OTel avoids lock-in to any observability backend.

### Golden signals, RED and USE
`core` · Related: Cloud Monitoring, SLI/SLO/SLA
**What:** Frameworks for choosing what to measure. **Four golden signals** (Google SRE): **latency**, **traffic**, **errors**, **saturation**. **RED** (for services): **R**ate, **E**rrors, **D**uration. **USE** (for resources): **U**tilization, **S**aturation, **E**rrors.
**How:** Alert on user-facing symptoms (golden signals and SLO burn), and use resource metrics (USE) for diagnosis and capacity.
**Watch out:** For LLM apps, add tokens per request, time to first token, cost per request, refusal and guardrail-block rates, and evaluation scores.

### Alerting practice
`working` · Related: Burn rate alerting, Incident management
**What:** Good alerts are **actionable** (a human must do something), **symptom-based** (users are affected) and **urgent-only** for pages. Everything else becomes a ticket or a dashboard. Each alert links a **playbook / runbook**.
**Watch out:** Alert fatigue (too many noisy alerts) is how real incidents get missed.

### Incident management and postmortems
`working` · Related: Alerting, Operational resilience
**What:** A structured response: detect → declare → assign roles (**incident commander**, communications lead, operations) → mitigate first (roll back, fail over, shed load) → resolve → **blameless postmortem** (timeline, root and contributing causes, action items with owners).
**Watch out:** Mitigate before debugging. Rolling back a bad release beats investigating while customers wait. Banks must also meet regulatory incident-reporting duties.

### Toil
`aware` · Related: Infrastructure as code, Automation
**What:** SRE term for manual, repetitive, automatable operational work that scales with the service and has no lasting value. SRE practice caps toil (for example at 50% of time) and automates the rest.

### Quotas, limits and capacity planning
`working` · Related: Reservations, Autoscaling
**What:** **Quotas** cap how much of a resource a project can use. **Rate quotas** limit API calls per minute (including Gemini requests and tokens per minute). **Allocation quotas** limit the count of resources (CPUs per region, IP addresses). They can usually be raised through a request. **System limits** are hard ceilings. **Capacity planning** forecasts demand and ensures headroom: quota increases, **reservations** (guaranteed VM or GPU capacity in a zone), committed use discounts, and Provisioned Throughput for models.
**Watch out:** Hitting a quota during a peak or a DR failover is a common, avoidable outage. Pre-raise quotas in DR regions too.

### Load testing and chaos engineering
`working` · Related: Disaster recovery, SLOs
**What:** **Load testing:** generate realistic traffic to find capacity limits and bottlenecks before users do (Locust, k6, JMeter; distributed on GKE). **Chaos engineering:** deliberately inject failures (kill instances, add latency, fail a zone or dependency) in a controlled way, to verify that resilience mechanisms actually work.
**GCP:** Fault injection in the load balancer or service mesh, stopping zones in DR tests, failing over Cloud SQL deliberately. It aligns with the operational resilience requirement to **test against severe but plausible scenarios**.

### Deployment strategies
`core` · Related: Cloud Run traffic splitting, Cloud Deploy, Feature flags
**What:** **Recreate:** stop the old, start the new (downtime). **Rolling:** replace instances gradually. **Blue/green:** run the new version alongside the old, switch all traffic at once, keep blue for instant rollback. **Canary:** send a small percentage of traffic to the new version, watch the metrics, then increase. **A/B testing:** split by user segment to compare behaviour. **Shadow / mirroring:** send a copy of real traffic to the new version without returning its responses. **Feature flags:** deploy code dark and toggle behaviour at runtime, which separates *deploy* from *release*.
**GCP:** Cloud Run revisions + traffic splitting + tags. GKE through Deployments, the Gateway API and Cloud Deploy canaries. MIG rolling updates. Load balancer weighted backends and traffic mirroring.
**Watch out:** Database schema changes need the **expand → migrate → contract** approach, so old and new versions both work during rollout.

### CI/CD
`core` · Related: Cloud Build, Cloud Deploy, Software supply chain security
**What:** **Continuous Integration:** every change is merged frequently and automatically built and tested (unit tests, linters, SAST, dependency and container scanning). **Continuous Delivery:** every change is *releasable*, promoted through environments by an automated pipeline, often with approval gates. **Continuous Deployment:** every passing change goes to production automatically. This all sits inside the **SDLC** (software development life cycle): plan → design → build → test → release → operate, with security built into every stage ("shift left").
**GCP:** Source (GitHub, GitLab, Bitbucket, Secure Source Manager) → **Cloud Build** (CI) → **Artifact Registry** (images + SBOM + provenance) → **Binary Authorization** → **Cloud Deploy** (CD across dev → test → prod targets, with approvals and canaries) → GKE or Cloud Run. Or GitHub Actions authenticating with Workload Identity Federation.

### Build-time vs runtime secrets
`working` · Related: Secret Manager, CI/CD, Container images
**What:** **Build-time** secrets are needed to *build* (for example a token for a private package registry). Use them in the build step only, from Secret Manager, and never let them end up in image layers. **Runtime** secrets are needed by the running app (database passwords, API keys). Inject them at deploy or run time (Cloud Run or GKE secret mounts, Secret Manager API) so the same image works in every environment and rotation doesn't need a rebuild.
**Watch out:** `docker history` exposes values passed as build arguments or copied into earlier layers. Scan images for secrets.

### Cloud Build
`working` · Related: CI/CD, Workload Identity Federation, Private pools
**What:** Serverless CI. Builds run as a series of **steps** (each a container) defined in `cloudbuild.yaml`, triggered by git events, Pub/Sub, webhooks or manually. It produces images and artifacts with **SLSA provenance**.
**How:** Runs as a configurable service account (least privilege). **Private pools** run builds inside your VPC with no public internet access, required by many banks to reach private repositories and artifact proxies.

### Cloud Deploy
`working` · Related: CI/CD, Deployment strategies
**What:** Managed **continuous delivery** to GKE, Cloud Run and GKE-attached clusters. You define a **delivery pipeline** of ordered **targets** (environments). **Releases** are promoted through them with **approvals**, automated or manual **canary** and blue/green strategies, verification jobs, rollbacks, and full audit history. It uses Skaffold for rendering and deploying.

### Infrastructure as code (IaC)
`core` · Related: Terraform state, GitOps, Landing zone
**What:** Defining infrastructure in version-controlled code instead of console clicks. You get repeatability, code review, audit trail, drift detection and rebuild-from-scratch DR.
**How:** **Declarative** tools (Terraform, Config Connector) describe the desired end state, and the tool works out the changes (**plan**) and applies them. **Imperative** scripts (gcloud) describe steps.
**GCP:** **Terraform** (the industry default, with the `google` provider), **Infrastructure Manager** (Google-managed Terraform runs, state and history), **Config Connector** (GCP resources as Kubernetes custom resources), **Cloud Foundation Fabric / FAST** (opinionated modules and a staged enterprise org bootstrap) and the Cloud Foundation Toolkit.

### Terraform state, plan and drift
`working` · Related: Infrastructure as code
**What:** **State** is Terraform's record mapping code to real resources. Keep it in a **remote backend** (a GCS bucket with versioning; locking prevents concurrent applies). **Plan** shows the diff before **apply**. **Drift** happens when someone changes resources outside Terraform.
**Watch out:** State can contain secrets. Restrict access to the state bucket, encrypt it with CMEK, and never commit it to git. Run Terraform from a pipeline with an impersonated service account, never from laptops with personal Owner rights.

### GitOps
`working` · Related: Infrastructure as code, Fleets, CI/CD
**What:** Git is the single source of truth for desired state. An agent in the cluster (**Config Sync**, **Argo CD**, Flux) continuously pulls and reconciles, so changes happen only through reviewed pull requests, and drift is corrected automatically.

### Immutable infrastructure and configuration management
`working` · Related: Images, Containers, Deployment strategies
**What:** Instead of patching running servers in place, **build a new image or container and replace** the instances. This removes configuration drift and makes rollback trivial. Configuration is injected at deploy time (env vars, Secret Manager, ConfigMaps), never baked per environment into the image.

### Environments and promotion
`working` · Related: CI/CD, Projects strategy
**What:** Separate **dev → test/UAT → pre-prod → prod** environments, usually separate projects (or folders), each with its own IAM, network and data. The *same artifact* (image digest) is promoted through them. In banks, prod data generally can't be used in lower environments without masking or synthetic replacement. **Ephemeral environments** (spun up per pull request from IaC, then destroyed) give realistic testing without permanent cost.

### Testing types
`working` · Related: CI/CD, Load testing, LLM evaluation
**What:** **Unit** (functions in isolation), **integration** (with real or emulated dependencies; GCP has **emulators** for Pub/Sub, Firestore, Bigtable, Spanner and Datastore, run through `gcloud emulators` or **Cloud Code** in the IDE), **contract** (consumer and provider API expectations), **end-to-end**, **performance / load**, **security** (SAST, DAST, dependency scanning, pen tests), **DR tests**. **Evaluation suites** for LLM and agent behaviour are an AI-specific addition.

### Active Assist and recommenders
`working` · Related: Rightsizing, Policy Intelligence
**What:** Machine-learning-driven recommendations across GCP: idle VMs, disks and IPs, VM rightsizing, committed-use purchases, IAM excess permissions, unattended projects, and network and security improvements. They're available through the console, API and the BigQuery export.

### Gemini Cloud Assist
`aware` · Related: Observability, Active Assist
**What:** An AI assistant in the Google Cloud console that helps design architectures, explain resources and costs, troubleshoot (investigations that analyze logs, metrics and configuration) and generate configurations. It appears in the newer exam guides. It's useful, but always verify its suggestions.

### App Hub and Cloud Hub
`aware` · Related: Cloud Asset Inventory, Observability
**What:** **App Hub** groups resources across projects into *applications* (services and workloads with owners, criticality and environment attributes), so monitoring, cost and governance can be organised by application rather than by project. **Cloud Hub** is a console home that shows application health, active incidents, deployments, quotas and other operational signals in one place. Both appear in the newer exam guides.

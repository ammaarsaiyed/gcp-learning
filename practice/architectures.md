# Architecture library

18 reference architectures. Most are written for a UK bank, and many involve AI. Each is used in two ways:

1. **Here, as reading:** each node has its role and *why that service was chosen*.
2. **In the practice app (`app/index.html`):** the service labels are hidden. Click each box to name it, then read the reasoning.

Format, which the app parses (keep it when adding your own):
`- id | label | category | col,row | why`. Category `fixed` = always shown (users, external systems).
`- from > to | edge label`.

---

## Arch: Static site and API (serverless starter)
id: serverless-starter
level: starter
context: A small internal web tool. A static frontend, a JSON API, a document database, a custom domain with HTTPS. Low, spiky traffic, so it should cost almost nothing when idle.
nodes:
- users | Staff browsers | fixed | 0,1 | The clients.
- dns | Cloud DNS | network | 1,1 | Authoritative DNS for the tool's domain, pointing at the load balancer's anycast IP.
- lb | Global external Application Load Balancer | network | 2,1 | One HTTPS front door with a managed certificate. A URL map sends `/api/*` to Cloud Run and everything else to the bucket.
- cdn | Cloud CDN | network | 2,0 | Caches the static assets at Google's edge, which cuts latency and egress.
- bucket | Cloud Storage | data | 4,0 | A backend bucket holding the built frontend (HTML/JS/CSS). Object storage is the cheapest way to serve static files.
- run | Cloud Run | compute | 4,2 | Runs the API container behind a serverless NEG. Scales to zero, so it's nearly free when idle.
- db | Firestore | data | 6,2 | A serverless document database with no capacity to manage, which suits a small app's JSON records.
edges:
- users > dns | resolve name
- users > lb | HTTPS
- lb > cdn | cache static
- cdn > bucket | backend bucket
- lb > run | /api/* (serverless NEG)
- run > db | client library + service account

## Arch: Internal policy assistant (RAG)
id: rag-policy-assistant
level: core
context: Colleagues ask questions about internal policies (around 20k PDFs) and get answers with citations. Staff only. Documents are Confidential. Answers must cite the policy section. New policy versions arrive daily.
nodes:
- staff | Colleagues (managed devices) | fixed | 0,1 | The users, signing in with corporate identity.
- iap | Identity-Aware Proxy | identity | 1,1 | Authenticates staff with the corporate IdP and checks IAM and device context before any request reaches the app. No VPN needed.
- app | Cloud Run | compute | 2,1 | Hosts the chat UI and the ADK agent that orchestrates retrieval and generation. Stateless, so it scales on demand.
- armor | Model Armor | security | 3,0 | Screens prompts and responses for prompt injection, jailbreaks and sensitive data before and after the model call.
- llm | Gemini on Agent Platform | ai | 4,0 | Generates the grounded answer from the retrieved chunks, through the enterprise endpoint (IAM, VPC-SC, regional processing).
- vec | AlloyDB (pgvector + ScaNN) | data | 4,2 | Stores chunk embeddings next to metadata (policy ID, version, effective date, access group), so a single SQL query does vector search plus permission and version filters.
- docs | Cloud Storage | data | 0,3 | Landing bucket for policy PDFs (CMEK, uniform access, versioning).
- trig | Eventarc | integration | 1,3 | Fires on object-finalize, so a new document version triggers re-indexing with no polling.
- ingest | Cloud Run jobs | compute | 2,3 | The ingestion pipeline: layout-aware parsing, structure-aware chunking, embedding, and an upsert into AlloyDB.
- emb | Embeddings model (Agent Platform) | ai | 3,3 | Turns each chunk (and each query) into a vector. The same model must be used for both.
- obs | Cloud Trace + Cloud Logging | ops | 3,2 | One trace per question (retrieval span, model span) and structured logs for evaluation and audit. The logs are PII-controlled.
edges:
- staff > iap | HTTPS (SSO)
- iap > app | signed JWT header
- app > armor | screen prompt
- armor > llm | generate (grounded)
- app > vec | similarity + ACL filter
- app > obs | spans, logs
- docs > trig | object finalized
- trig > ingest | start job
- ingest > emb | embed chunks
- ingest > vec | upsert vectors

## Arch: Mobile banking API (serverless, customer-facing)
id: mobile-banking-api
level: core
context: The mobile app needs balances, transactions and payee management. Spiky load (payday, salary mornings), strict security, APIs shared with partners later. Account data is mastered in a cloud-native ledger database.
nodes:
- app | Mobile app | fixed | 0,1 | Customer devices.
- armor | Cloud Armor | security | 1,0 | WAF (OWASP rules), rate limiting and L7 DDoS protection at Google's edge, before traffic reaches the gateway.
- lb | Global external Application Load Balancer | network | 1,1 | Anycast IP, TLS 1.2+ (SSL policy), and the attachment point for Cloud Armor.
- apigee | Apigee | integration | 2,1 | API management: OAuth token validation, per-app quotas and spike arrest, threat protection, analytics, and API products ready for partner exposure later.
- bff | Cloud Run | compute | 3,1 | A backend-for-frontend that aggregates calls for mobile screens. Autoscales for payday spikes.
- cache | Memorystore | data | 4,0 | Caches read-heavy, slow-changing data (payee lists, product info) to protect the database at peaks.
- ledger | Spanner | data | 4,2 | A strongly consistent, horizontally scalable relational database for accounts and transactions, with 99.99%+ availability.
- events | Pub/Sub | integration | 5,1 | Publishes "payee added" and "payment made" events so notifications and fraud checks don't slow the user's request.
- notify | Cloud Run functions | compute | 6,1 | Consumes events and sends push notifications. Decoupled and independently scalable.
edges:
- app > lb | HTTPS
- lb > armor | security policy
- lb > apigee | PSC / internal routing
- apigee > bff | verified request
- bff > cache | cache-aside reads
- bff > ledger | read/write txns
- bff > events | publish event
- events > notify | push subscription

## Arch: Hybrid landing zone (bank network)
id: hybrid-landing-zone
level: core
context: The bank's on-prem data centres must reach GCP workloads privately, with high availability. A central network team controls networking, and app teams deploy in their own projects. Internet egress must be controlled, and Google APIs reached privately.
nodes:
- dc | On-prem data centres | fixed | 0,1 | The existing estate (core banking, AD, DNS).
- ic | Dedicated Interconnect | network | 1,1 | Private 10/100G circuits in London colocation facilities. Four connections across two metros give the 99.99% topology.
- router | Cloud Router | network | 2,1 | BGP sessions with on-prem routers over the VLAN attachments. It learns on-prem prefixes and advertises cloud subnets dynamically.
- host | Shared VPC host project | network | 3,1 | Central network team owns subnets, routes and firewalls. App teams get Network User on specific subnets only (separation of duties).
- svc | Service projects | compute | 4,2 | App teams' projects, with workloads attached to the shared subnets. IAM and billing stay per app.
- fw | Hierarchical firewall policies | security | 3,0 | Org- or folder-level rules app teams can't override (for example deny SSH from the internet, allow the scanner range).
- dns | Cloud DNS | network | 2,3 | Forwarding zones to on-prem DNS for corp names, an inbound policy so on-prem can resolve cloud private zones, and private zones for googleapis.com.
- psc | Private Service Connect endpoint | network | 4,0 | Private IP for Google APIs (Gemini, BigQuery, Cloud Storage), reachable from on-prem over the Interconnect and inside the VPC-SC perimeter.
- swp | Secure Web Proxy | security | 5,1 | Explicit egress proxy that allows only approved external hostnames, with full request logging.
- nat | Cloud NAT | network | 6,1 | Outbound internet with fixed IPs for the proxied traffic. Nothing inbound.
edges:
- dc > ic | private circuits
- ic > router | VLAN attachments (BGP)
- router > host | dynamic routes
- host > svc | shared subnets
- fw > host | enforced on VPC
- dc > dns | DNS forwarding
- host > psc | private API access
- svc > swp | egress via proxy
- swp > nat | to internet

## Arch: Real-time card fraud scoring
id: realtime-fraud
level: advanced
context: Card authorisations must be scored for fraud in under 100 ms. Features like "spend in the last 10 minutes" must be fresh. Decisions are stored for analytics, model monitoring and investigator review.
nodes:
- switch | Card authorisation switch (on-prem) | fixed | 0,1 | The payment switch asking "approve or decline?".
- api | Cloud Run (scoring service) | compute | 1,1 | A low-latency synchronous API, reached privately over Interconnect, that fetches features, calls the model and returns a decision within the latency budget. Min instances avoid cold starts.
- feat | Bigtable | data | 2,0 | Single-digit-millisecond key lookups of per-card features (row key = card hash). The online feature store.
- model | Agent Platform endpoint | ai | 2,2 | Serves the fraud model (for example a gradient-boosted tree) online, autoscaling, privately through PSC.
- bus | Pub/Sub | integration | 3,1 | Each transaction and decision is published as an event, which decouples analytics and feature updates from the hot path.
- flow | Dataflow (streaming) | compute | 4,0 | Computes windowed aggregates (spend per card over 10 minutes and 24 hours) from the event stream and writes them back to Bigtable.
- bq | BigQuery | data | 4,2 | All decisions and features for analytics, model retraining, monitoring and investigations.
- mon | Model Monitoring | ai | 5,2 | Detects feature drift and skew against the training baseline, and alerts model risk owners.
- looker | Looker | ops | 5,1 | Dashboards for fraud ops (decline rates, alert volumes, false positives).
edges:
- switch > api | score request (<100ms)
- api > feat | get features
- api > model | predict
- api > bus | publish decision
- bus > flow | stream events
- flow > feat | update aggregates
- bus > bq | BigQuery subscription
- bq > mon | baseline vs live
- bq > looker | dashboards

## Arch: Core banking CDC to a governed lakehouse
id: cdc-lakehouse
level: core
context: An on-prem core banking database (Oracle) must feed near-real-time analytics and ML without loading the source system. Data includes PII. Analysts need curated, governed datasets with lineage for regulatory reporting.
nodes:
- core | Core banking DB (on-prem Oracle) | fixed | 0,1 | The system of record.
- ds | Datastream | integration | 1,1 | Serverless change data capture from Oracle redo logs. Low impact on the source, near real time.
- raw | BigQuery (raw / bronze) | data | 2,1 | Datastream writes changes straight into BigQuery replica tables.
- sdp | Sensitive Data Protection | security | 3,0 | Discovers and classifies PII columns, and de-identifies or tokenizes them for wider-access layers.
- dform | Dataform | integration | 3,1 | Version-controlled SQL transformations (bronze → silver → gold) with assertions as data-quality tests.
- gold | BigQuery (curated / gold) | data | 4,1 | Modelled, documented datasets. Policy tags give column-level security, and row-level security applies by region or business unit.
- plex | Dataplex Universal Catalog | ops | 4,0 | Catalog, business glossary, column-level lineage and data-quality scans, which back BCBS 239-style "where did this number come from?" evidence.
- looker | Looker | ops | 5,1 | A governed semantic layer and dashboards for regulatory and management reporting.
- bqml | BigQuery ML | ai | 5,2 | Trains and runs models in SQL directly on curated data (for example churn or propensity).
edges:
- core > ds | redo log CDC
- ds > raw | stream changes
- raw > dform | transform
- sdp > raw | scan + classify
- dform > gold | publish curated
- plex > gold | catalog, lineage, DQ
- gold > looker | semantic model
- gold > bqml | train / predict

## Arch: Agentic customer-service assistant (tools, MCP, A2A)
id: agentic-servicing
level: advanced
context: A chat assistant in the banking app helps customers with card controls, statements and simple disputes. It must take real actions only with confirmation, delegate mortgage questions to the mortgage team's agent, and hand off to a human.
nodes:
- cust | Customer (in app chat) | fixed | 0,1 | An authenticated customer session.
- gw | Apigee | integration | 1,1 | The AI gateway: validates the customer token, enforces token quotas per channel, logs every model and tool call.
- agent | Agent Runtime (ADK orchestrator) | ai | 2,1 | Hosts the ADK agent with managed sessions and memory. It plans, calls tools and asks for confirmation before actions.
- llm | Gemini on Agent Platform | ai | 3,0 | Reasoning and tool selection for the orchestrator.
- armor | Model Armor | security | 2,0 | Screens inputs and outputs for prompt injection (including from tool results) and PII leakage.
- mcp | MCP server on Cloud Run | compute | 3,2 | Exposes approved banking tools (freeze card, get statement) through MCP with narrow schemas, and calls internal APIs under its own least-privilege service account.
- core | Card and account APIs (on-prem) | fixed | 4,2 | Existing systems of record, reached privately.
- a2a | Mortgage agent (A2A) | ai | 4,1 | Owned by another team, it publishes an Agent Card. The orchestrator delegates mortgage tasks over the A2A protocol instead of reimplementing them.
- human | Contact-centre handoff (Customer Engagement Suite) | integration | 5,1 | Escalates to a human agent with the conversation summary when confidence is low or the customer asks.
- trace | Cloud Trace + BigQuery eval logs | ops | 5,0 | Trajectory traces (each model and tool step) feed offline evaluation and audit.
edges:
- cust > gw | chat message
- gw > agent | authorised request
- agent > armor | screen in/out
- agent > llm | plan / respond
- agent > mcp | tool call (after confirm)
- mcp > core | private API call
- agent > a2a | delegate task (A2A)
- agent > human | escalate
- agent > trace | spans

## Arch: Three-tier lift-and-shift with high availability
id: three-tier-ha
level: starter
context: A Java web application on 12 on-prem VMs with MySQL has to move within 3 months, with minimal code change and 99.9% availability. Patches need internet access. Admins need SSH.
nodes:
- users | Users | fixed | 0,1 | Internet users.
- armor | Cloud Armor | security | 1,0 | WAF at the edge.
- elb | Global external Application Load Balancer | network | 1,1 | HTTPS front door with health checks.
- web | Regional managed instance group (web) | compute | 2,1 | Web tier VMs spread across 3 zones, with autoscaling and autohealing, from a hardened instance template.
- ilb | Internal Application Load Balancer | network | 3,1 | Private L7 load balancing from the web tier to the app tier.
- appt | Regional managed instance group (app) | compute | 4,1 | The application tier, also multi-zone.
- sql | Cloud SQL for MySQL (HA) | data | 5,1 | Managed MySQL with a synchronous standby in another zone (automatic failover), automated backups and PITR. Migrated with Database Migration Service.
- replica | Cross-region read replica | data | 5,2 | Asynchronous replica in a second region, promoted for disaster recovery.
- nat | Cloud NAT | network | 3,2 | Outbound access for OS patches. The VMs have no external IPs.
- iap | IAP TCP forwarding | identity | 2,2 | Admin SSH by IAM identity with no bastion or public IPs (OS Login).
edges:
- users > elb | HTTPS
- elb > armor | policy
- elb > web | backend service
- web > ilb | internal HTTP
- ilb > appt | backend service
- appt > sql | private IP
- sql > replica | async replication
- web > nat | patches out
- iap > web | SSH (IAM)

## Arch: Secure data science environment
id: secure-data-science
level: advanced
context: Data scientists analyse customer data for models. Data must stay in the UK and inside the bank's projects. Exfiltration to personal projects or the internet must be impossible even with valid credentials. Access only from bank-managed devices. Every data read must be auditable.
nodes:
- ds | Data scientists (managed devices) | fixed | 0,1 | Users on bank laptops.
- acm | Access Context Manager | identity | 1,0 | Defines an access level: bank-managed device + corporate IP ranges. The perimeter admits only matching requests.
- vpcsc | VPC Service Controls perimeter | security | 1,1 | Wraps the analytics projects. API calls crossing the perimeter boundary are blocked, which stops copying data out even with valid IAM.
- wb | Agent Platform Workbench | compute | 2,1 | Managed notebooks in a private VPC (no public IP), running as a per-user or per-team service account.
- bq | BigQuery | data | 3,1 | Customer datasets in the London region, with column-level policy tags (PII masked for most roles) and row-level security.
- gcs | Cloud Storage | data | 3,2 | Model artifacts and extracts, with CMEK and uniform access.
- kms | Cloud KMS (CMEK) | security | 4,0 | Bank-controlled keys (HSM-backed) for BigQuery and Cloud Storage. Revoking a key makes the data unreadable.
- logs | Cloud Audit Logs (Data Access) | ops | 4,2 | Data Access logs enabled for BigQuery and Cloud Storage, routed by an aggregated sink to a locked central logging project.
- orgp | Organization Policy | security | 2,0 | Resource locations limited to UK, no external IPs, no service account keys, domain-restricted sharing.
edges:
- ds > acm | request context
- acm > vpcsc | access level
- vpcsc > wb | allowed ingress
- wb > bq | query (restricted VIP)
- wb > gcs | read/write
- kms > bq | wraps keys
- kms > gcs | wraps keys
- bq > logs | data access events
- orgp > wb | guardrails

## Arch: Secure software supply chain (CI/CD)
id: secure-cicd
level: core
context: Teams deploy containers to GKE and Cloud Run. The bank requires no long-lived credentials, build provenance, vulnerability gates, approval before production, and an audit trail of every deployment.
nodes:
- dev | Developer pull request | fixed | 0,1 | A code change, reviewed in the git platform.
- gh | GitHub | fixed | 1,1 | Source control with branch protection.
- wif | Workload Identity Federation | identity | 1,0 | Pipelines authenticate to GCP with short-lived federated tokens restricted to the bank's repos and branches. No service account keys.
- build | Cloud Build (private pool) | compute | 2,1 | Builds and tests inside the bank's VPC (no public internet), and emits SLSA provenance.
- ar | Artifact Registry | data | 3,1 | Stores images by digest, with remote repositories proxying approved public dependencies.
- scan | Artifact Analysis | security | 3,0 | Scans images for CVEs on push and continuously. Critical findings block promotion.
- binauthz | Binary Authorization | security | 4,0 | Admission policy: only images with valid build provenance and attestations from the bank's pipeline can run.
- deploy | Cloud Deploy | ops | 4,1 | Promotes the same image digest dev → test → prod, with approvals, canary strategy and full audit history.
- prod | GKE / Cloud Run (prod) | compute | 5,1 | Runtime targets. Deployments happen only through the pipeline's service account.
- sm | Secret Manager | security | 5,2 | Runtime secrets are injected at deploy time, never built into images.
edges:
- dev > gh | merge
- gh > build | trigger
- wif > build | federated auth
- build > ar | push image + provenance
- ar > scan | scan
- ar > deploy | release by digest
- deploy > prod | canary / promote
- binauthz > prod | admission check
- sm > prod | inject secrets

## Arch: KYC document onboarding (event-driven)
id: kyc-onboarding
level: core
context: New customers upload ID documents and proof of address. Extract the fields, check consistency, create a case, and route uncertain cases to a human reviewer within hours. Every step must be auditable and retryable.
nodes:
- cust | Customer (web/app) | fixed | 0,1 | Uploads documents.
- surl | Signed URL upload | identity | 1,1 | The app issues a short-lived signed URL, so the browser uploads straight to the bucket and files never pass through the API servers.
- gcs | Cloud Storage | data | 2,1 | Uploaded documents in a CMEK bucket with retention policies.
- evt | Eventarc | integration | 3,1 | The object-finalize event starts processing.
- wf | Workflows | integration | 4,1 | Orchestrates the steps with retries and error handling, and waits on a callback for human review when needed (it can wait for days).
- docai | Document AI | ai | 4,0 | ID document and proof-of-address processors extract structured fields with confidence scores.
- gem | Gemini on Agent Platform | ai | 5,0 | Cross-checks the extracted fields (name and address consistency), summarises discrepancies and drafts the reviewer note.
- fs | Firestore | data | 5,2 | The case record (status, extracted fields, decisions) for the onboarding app and the reviewers.
- tasks | Cloud Tasks | integration | 4,2 | A rate-limited queue that pushes uncertain cases to the case-management system without overloading it.
- bus | Pub/Sub | integration | 6,1 | Publishes "kyc.completed" for downstream account opening and analytics.
edges:
- cust > surl | get upload URL
- surl > gcs | PUT document
- gcs > evt | finalized
- evt > wf | start execution
- wf > docai | extract
- wf > gem | verify + summarise
- wf > fs | update case
- wf > tasks | queue review
- wf > bus | publish outcome

## Arch: Multi-region active-active payments API
id: active-active-payments
level: advanced
context: A payment-initiation API with an impact tolerance of 15 minutes, so it must survive a full region outage with no data loss. Writes must be strongly consistent. Regulatory policy allows the EU region as a pair for this service.
nodes:
- clients | Payment initiators | fixed | 0,1 | Apps and partners.
- dns | Cloud DNS | network | 1,0 | Public name for the API.
- lb | Global external Application Load Balancer | network | 1,1 | A single anycast IP that routes to the nearest healthy region and fails over automatically when a region's backends fail health checks.
- runa | Cloud Run (europe-west2) | compute | 2,0 | Region A API instances (serverless NEG).
- runb | Cloud Run (europe-west1) | compute | 2,2 | Region B API instances, serving live traffic too (active-active, not standby).
- spanner | Spanner (multi-region config) | data | 4,1 | Synchronous Paxos replication across regions gives RPO 0 and strongly consistent writes from both regions. It's the piece that makes active-active safe for money.
- idem | Idempotency key store (in Spanner) | data | 4,0 | Stores idempotency keys transactionally with each payment, so client retries after a failover never double-pay.
- bus | Pub/Sub | integration | 5,1 | A global topic for payment events to downstream systems, with a message storage policy restricting regions.
edges:
- clients > dns | resolve
- clients > lb | HTTPS
- lb > runa | nearest healthy
- lb > runb | nearest healthy
- runa > spanner | read/write txn
- runb > spanner | read/write txn
- runa > idem | check key
- spanner > bus | change stream → events

## Arch: Central logging and security operations
id: central-logging-secops
level: core
context: Hundreds of projects. The SOC needs every audit and security log centrally, tamper-resistant, kept for 7 years, searchable, and fed to the SIEM. Platform teams need alerting on SLOs and security findings.
nodes:
- projects | All projects (org) | fixed | 0,1 | Every workload project emits logs.
- sink | Aggregated log sink (org level) | ops | 1,1 | One org-level sink captures audit logs from all child projects. Teams can't bypass it.
- bucket | Locked log bucket (logging project) | data | 2,1 | Central log bucket with locked retention and restricted access, and Log Analytics enabled for SQL queries.
- bq | BigQuery (linked dataset) | data | 3,2 | SQL analytics over logs for investigations and audit evidence.
- ps | Pub/Sub | integration | 3,0 | Streams logs in near real time to the SIEM.
- siem | Google Security Operations / SIEM | fixed | 4,0 | The SOC's detection and response platform.
- scc | Security Command Center | security | 1,3 | Misconfiguration and threat findings across the org, exported through Pub/Sub to the SIEM.
- mon | Cloud Monitoring (alerting) | ops | 4,2 | SLO burn-rate alerts and log-based metrics (for example break-glass account use) → notification channels.
- pager | PagerDuty / on-call | fixed | 5,2 | On-call engineers.
edges:
- projects > sink | audit + app logs
- sink > bucket | route
- bucket > bq | linked dataset
- sink > ps | route (SIEM filter)
- ps > siem | stream
- scc > ps | findings
- projects > mon | metrics
- mon > pager | page

## Arch: Private Gemini access from on-premises apps
id: private-gemini-onprem
level: advanced
context: Existing on-prem applications want to call Gemini for summarisation. Traffic must not use the public internet, calls must stay inside the bank's VPC-SC perimeter, and DNS must resolve the Google API names to private addresses.
nodes:
- app | On-prem application | fixed | 0,1 | An existing service in the data centre.
- odns | On-prem DNS | fixed | 0,2 | The corporate resolvers.
- ic | Cloud Interconnect | network | 1,1 | Private connectivity into the hub VPC.
- cr | Cloud Router | network | 2,1 | Advertises the PSC endpoint IP to on-prem over BGP.
- inbound | Cloud DNS inbound server policy | network | 1,2 | An IP in the VPC that on-prem DNS forwards googleapis.com queries to.
- pzone | Cloud DNS private zone (googleapis.com) | network | 2,2 | Maps aiplatform.googleapis.com (and others) to the private endpoint IP.
- psc | Private Service Connect endpoint (Google APIs) | network | 3,1 | An internal IP in the hub VPC that fronts Google APIs, set to the VPC-SC-compatible bundle.
- perim | VPC Service Controls perimeter | security | 4,0 | The AI project sits inside the perimeter. Ingress rules admit the on-prem path (access level on source ranges) and the service account.
- gem | Gemini on Agent Platform | ai | 4,1 | The regional model endpoint, called with IAM-authenticated requests.
edges:
- app > ic | HTTPS to private IP
- odns > inbound | forward googleapis.com
- inbound > pzone | resolve
- ic > cr | BGP routes
- cr > psc | route to endpoint
- psc > gem | API call
- perim > gem | protects

## Arch: GKE microservices platform with a service mesh
id: gke-mesh-platform
level: advanced
context: 40 microservices from several teams. A shared platform with mTLS between services, per-service identity, GitOps deployments, Prometheus metrics and private databases.
nodes:
- users | Users | fixed | 0,1 | Clients.
- gw | GKE Gateway (external Application Load Balancer) | network | 1,1 | The Gateway API provisions the external load balancer. App teams own their HTTPRoutes.
- gke | GKE Autopilot (regional) | compute | 2,1 | Google-managed nodes across 3 zones. Teams deploy into namespaces.
- mesh | Cloud Service Mesh | security | 2,0 | Automatic mTLS, authorization policies ("only payments may call ledger"), retries and timeouts, and golden-signal telemetry.
- wi | Workload Identity Federation for GKE | identity | 3,0 | Each Kubernetes service account maps to an IAM principal, so Pods call Google APIs without keys.
- sql | Cloud SQL (private IP) | data | 3,2 | Relational data reached through the Cloud SQL Auth Proxy sidecar with IAM authentication.
- redis | Memorystore | data | 4,2 | Shared cache and session store.
- sync | Config Sync (GitOps) | ops | 1,3 | Reconciles cluster configuration and policies from git. Policy Controller blocks non-compliant manifests.
- prom | Managed Service for Prometheus | ops | 4,1 | Scrapes and stores Prometheus metrics without running Prometheus servers, queried with PromQL in Cloud Monitoring.
edges:
- users > gw | HTTPS
- gw > gke | HTTPRoute → Pods (NEG)
- mesh > gke | mTLS sidecars
- wi > gke | pod identity
- gke > sql | Auth Proxy
- gke > redis | cache
- sync > gke | desired state
- gke > prom | metrics

## Arch: Credit-risk model pipeline under model risk management
id: credit-risk-mlops
level: advanced
context: A probability-of-default model retrained monthly on bureau and account data. The model risk policy requires reproducible training, independent validation before use, explainability for adverse decisions, and drift monitoring.
nodes:
- bq | BigQuery (feature tables) | data | 0,1 | Curated, point-in-time-correct training data.
- fs | Agent Platform Feature Store | data | 1,0 | Shared feature definitions served consistently to training and scoring.
- comp | Cloud Composer | integration | 0,3 | A monthly schedule that orchestrates data refresh and triggers the pipeline.
- pipe | Agent Platform Pipelines | ai | 1,1 | A reproducible, versioned pipeline: data validation → train → evaluate → register, with lineage recorded in ML Metadata.
- reg | Model Registry | ai | 2,1 | The model inventory entry with version, metrics and lineage. Aliases (`challenger` / `champion`) are switched only after validation sign-off.
- val | Independent validation (2nd line) | fixed | 2,3 | Model validators review the evidence and approve or reject.
- batch | Batch prediction | ai | 3,1 | Monthly scoring of the whole book, written back to BigQuery.
- xai | Explainable AI | ai | 3,0 | Feature attributions per prediction give reason codes for adverse-action explanations.
- mon | Model Monitoring | ai | 4,2 | Tracks drift in feature and score distributions, and triggers review when thresholds are breached.
- out | BigQuery (scores) + Looker | ops | 4,1 | Scores and monitoring dashboards for risk committees.
edges:
- comp > pipe | trigger monthly
- bq > pipe | training data
- fs > pipe | features
- pipe > reg | register version
- reg > val | evidence pack
- reg > batch | approved model
- batch > xai | attributions
- batch > out | scores
- out > mon | drift checks

## Arch: Open Banking API platform (FAPI)
id: open-banking
level: advanced
context: Licensed third-party providers (TPPs) access account information and initiate payments with customer consent. FAPI security: mTLS client certificates, OAuth 2.0 with signed requests. The regulator expects high availability and full audit.
nodes:
- tpp | Third-party provider | fixed | 0,1 | A fintech app with eIDAS or OBIE certificates.
- lb | External Application Load Balancer (mTLS) | network | 1,1 | Requires and validates client certificates against a trust store of approved CAs (frontend mTLS). Cloud Armor rules apply too.
- apigee | Apigee | integration | 2,1 | The FAPI profile: OAuth 2.0 authorization server, certificate-bound tokens, consent checks, per-TPP quotas, analytics and the TPP developer portal.
- consent | Cloud Run (consent service) | compute | 3,0 | Manages customer consents (scopes, expiry, revocation) and the customer-facing consent journey.
- cdb | Cloud SQL (consents) | data | 4,0 | The relational consent store with an HA configuration and PITR.
- idp | Bank customer identity provider | fixed | 3,2 | Authenticates customers with strong customer authentication during consent.
- core | Account and payment APIs (on-prem) | fixed | 4,1 | Systems of record behind private connectivity.
- hsm | Cloud HSM (via Cloud KMS) | security | 2,0 | HSM-protected keys for signing tokens and responses (FIPS 140-2 Level 3).
- audit | Cloud Audit Logs + Apigee analytics | ops | 5,1 | Every TPP call and consent change, retained for the regulator.
edges:
- tpp > lb | mTLS
- lb > apigee | verified client cert
- apigee > consent | consent check
- consent > cdb | read/write
- consent > idp | SCA redirect
- apigee > core | private call
- hsm > apigee | sign tokens
- apigee > audit | logs

## Arch: Egress-controlled call to an external payment scheme
id: controlled-egress
level: core
context: A private service must call a payment scheme's API over the internet. The scheme allow-lists source IPs and requires mTLS. Security requires that this service can reach only that hostname and that every outbound request is logged.
nodes:
- svc | Cloud Run (payments adapter) | compute | 0,1 | A private service (internal ingress only) with no direct internet route.
- dve | Direct VPC egress | network | 1,1 | Sends all of the service's outbound traffic into the VPC, so network controls apply.
- swp | Secure Web Proxy | security | 2,1 | An explicit proxy policy that allows only the scheme's hostname for this service's identity, and logs every request.
- nat | Cloud NAT (manual static IPs) | network | 3,1 | Fixed, reserved public IPs that the scheme allow-lists.
- scheme | Payment scheme API | fixed | 4,1 | An external partner over the internet.
- cert | Secret Manager (client certificate) | security | 1,0 | Holds the mTLS client certificate and key for the scheme connection, with access audited and rotation tracked.
- fwp | Firewall policy (egress deny) | security | 2,2 | Denies all other egress from the subnet, so the proxy is the only way out.
edges:
- svc > dve | all egress
- dve > swp | via proxy
- swp > nat | allowed host only
- nat > scheme | mTLS from static IP
- cert > svc | mount client cert
- fwp > dve | default deny egress

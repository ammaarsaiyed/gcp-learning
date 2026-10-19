# Learning path

**Start here.** This is the order to learn everything in, from zero to designing bank-grade AI systems. Each lesson takes 25–45 minutes:

1. **Why it matters:** a short framing of the problem these concepts solve, and how they connect to what you already know.
2. **Concepts, one at a time:** read the term, explain it to yourself, reveal, rate. Each one you study joins your flashcard deck.
3. **Use it straight away:** a quiz, a diagram, a journey, a design lab or a review that combines the new concepts with earlier ones.
4. **Checkpoint:** explain one integrating question out loud. If you can't, revisit before moving on.

The path follows the order things depend on each other: how the cloud is organised → how networks move bits → who's allowed to do what → private networking on GCP → where code runs → where data lives → how services talk → running it reliably → AI → banking context → architecture. Later lessons assume earlier ones.

Do the lessons in the [practice app](../app/index.html) (Learn tab). It tracks progress and opens each practice item for you. This file is the source and doubles as a syllabus.

**Format** (parsed by `tools/build.py`): `concepts:` are atlas terms separated by `;` (a unique prefix is enough). `practice:` items are `quiz:<start of question>`, `diagram:<id>`, `journey:<id>`, `lab:<id>`, `review:<id>` or `read:<guide number>`.

---

## Stage: Foundations: how Google Cloud is organised
id: s1
summary: The containers everything lives in (organisation, folders, projects), where things physically run, who pays, and who is responsible for what.

### Lesson: The shape of Google Cloud
id: l01
minutes: 30
goal: Before any service makes sense you need the skeleton. Every resource lives in a **project**, projects sit in **folders** under an **organisation**, and policies flow downwards. Every resource also lives in a **location** (zone, region, multi-region), and that decides what failures it survives. Get these two ideas solid and half of "how GCP works" follows.
concepts: Resource hierarchy; Project strategy; Regions, zones and choosing a location; Failure domains: zones and regions; Shared responsibility model; Quotas and limits; Billing accounts and billing structure; Budgets and alerts
practice: diagram:serverless-starter; quiz:Which statement about budgets is true
checkpoint: Explain why a bank would create separate projects for "payments-dev" and "payments-prod", and what a zone outage would do to a single VM versus a regional service.

## Stage: How networks move bits
id: s2
summary: The networking fundamentals every cloud design rests on: addresses, routes, ports, connections, names, encryption, and the boxes that sit in the path.

### Lesson: Addresses, ranges and routes
id: l02
minutes: 35
goal: Every packet has a source and destination **IP address**. **CIDR** ranges group addresses into networks, and **routes** decide where packets go next. **Ports** pick the program on a machine, and **NAT** lets private machines talk to the internet. Cloud VPCs are built entirely from these ideas.
concepts: OSI and TCP/IP layers; IP address (IPv4; CIDR and subnetting; Private address ranges; Ports; Socket and the 5-tuple; Routing and route tables; Default route; NAT (Network
practice: read:01
checkpoint: Without notes, explain how a VM at 10.10.0.5 with no public IP can download a patch from the internet. Name each piece involved.

### Lesson: Connections, names and the web
id: l03
minutes: 35
goal: Before any data flows, **TCP** opens a connection with a handshake (that costs a round trip), **DNS** turns names into addresses, and **HTTP** carries requests and responses. Latency is mostly round trips multiplied by distance, which is why connection reuse and edge locations matter.
concepts: TCP; TCP three-way handshake; UDP; Latency, RTT; DNS; HTTP basics; HTTP/1.1 vs HTTP/2; Keep-alive and connection pooling; MTU and fragmentation; ICMP, ping
practice: quiz:Calls to an on-prem API over HA VPN work
checkpoint: Walk through everything that happens from typing a URL to the first byte of the page arriving: DNS, TCP, then the request.

### Lesson: Encryption and trust on the wire
id: l04
minutes: 40
goal: **TLS** turns a TCP connection into a private, authenticated one, using asymmetric cryptography to agree on keys and symmetric cryptography for speed. **Certificates** prove identity, and **mTLS** makes both sides prove it. This is the basis of "encryption in transit" and of zero trust between services.
concepts: Symmetric vs asymmetric; Hashing, HMAC; TLS (Transport; TLS handshake; Certificates and PKI; mTLS; TLS termination; Encryption in transit; SNI
practice: read:01
checkpoint: Explain the difference between TLS and mTLS, and why a payments partner API might require mTLS.

### Lesson: The boxes in the path: proxies, load balancers, firewalls
id: l05
minutes: 40
goal: Real traffic passes through **reverse proxies**, **load balancers**, **firewalls** and **CDNs**. Learn what each looks at (L4 vs L7), which direction it controls (**ingress/egress**), and where the **trust boundaries** are. These words come up in every architecture review.
concepts: Forward proxy vs reverse proxy; Load balancing (L4 vs L7); Firewall (stateful; Ingress and egress; North-south vs east-west; Network perimeter, DMZ; Network segmentation; CDN and edge caching; DDoS; Anycast; VPN and IPsec; BGP
practice: quiz:Which statement about GCP VPC firewall rules is true
checkpoint: For a customer-facing banking API, list the boxes a request passes through from the internet to the code, and say what each one checks.

## Stage: Identity and security
id: s3
summary: Who and what is allowed to do what. Tokens, IAM, identities for software, zero trust, encryption keys, perimeters and guardrails.

### Lesson: Proving who you are: authentication and tokens
id: l06
minutes: 40
goal: **Authentication** proves identity, and **authorization** decides permissions. On the web, identity travels as **tokens**: OAuth access tokens to call APIs, OIDC ID tokens to prove who you are, usually as **JWTs**. Nearly every "401 vs 403" bug and every SSO design comes back to these.
concepts: Authentication vs authorization; Identity provider (IdP); SAML 2.0; OAuth 2.0; OpenID Connect; JWT; Access tokens, ID tokens; API keys; Multi-factor
practice: quiz:A Cloud Run service returns 401 when another
checkpoint: Explain what's inside a JWT, how a service verifies one, and why checking the audience matters.

### Lesson: IAM on Google Cloud
id: l07
minutes: 40
goal: GCP authorization is one sentence: **a principal gets a role on a resource**, and grants inherit down the hierarchy. Groups, least privilege, conditions and deny policies are how organisations keep that safe at scale.
concepts: Cloud Identity, Google Workspace; Principals; IAM roles; IAM policies and inheritance; Groups and access reviews; IAM Conditions; IAM deny policies; Least privilege, separation; RBAC vs ABAC; Policy Intelligence
practice: quiz:A user is granted Editor on a folder; quiz:Which of these can be used to enforce security
checkpoint: A contractor needs read access to one bucket until Friday. Describe the exact grant (principal, role, resource, condition) and why it's least privilege.

### Lesson: Identities for software
id: l08
minutes: 40
goal: Code needs identities too. **Service accounts** are attached to workloads, client libraries find credentials automatically (**ADC** via the **metadata server**), and nothing outside GCP should hold a key: it uses **Workload Identity Federation**. This is where most real-world cloud breaches start.
concepts: Service accounts; Service account keys; Application Default Credentials; Metadata server; Service account impersonation; Workload Identity Federation; Workload Identity Federation for GKE; Workforce Identity Federation
practice: journey:j-identity; quiz:GitHub Actions must deploy to GCP; quiz:Your code runs on Cloud Run and on developers
checkpoint: Trace how code on Cloud Run gets permission to read BigQuery without any key, from the metadata server to the IAM check.

### Lesson: Zero trust access for people
id: l09
minutes: 30
goal: Banks no longer trust "being on the network". **IAP** puts identity and device checks in front of every app and VM, **access levels** add context, and **PAM** gives admin rights only for a limited time, with approval.
concepts: Identity-Aware Proxy; Zero trust and BeyondCorp; Access Context Manager; Context-aware access; Privileged Access Manager; OS Login; Identity Platform
practice: quiz:An internal web tool needs to be reachable by employees; quiz:Engineers occasionally need Owner
checkpoint: Explain how a colleague on a bank laptop reaches an internal app with no VPN, and what stops someone on a personal laptop.

### Lesson: Protecting data with encryption and secrets
id: l10
minutes: 40
goal: Everything is encrypted at rest by default, so the real question is **who controls the keys**. Learn envelope encryption, Cloud KMS, CMEK, HSM and EKM, and where secrets belong (never in code).
concepts: CIA triad; Defense in depth; Encryption at rest; Envelope encryption; Cloud KMS; CMEK; Cloud HSM; Cloud EKM; Key rotation; Secret Manager; Confidential Computing
practice: quiz:The CISO asks
checkpoint: Explain envelope encryption, and what happens to a BigQuery dataset if its CMEK key is disabled.

### Lesson: Guardrails, perimeters and detection
id: l11
minutes: 45
goal: IAM controls *who*. **Org policies** control *what's allowed at all*, **VPC Service Controls** control *where data can go*, and **audit logs** and **Security Command Center** tell you *what happened*. Together they make up a bank's security baseline.
concepts: Organization Policy Service; VPC Service Controls; Data residency vs data sovereignty; Cloud Audit Logs; Log sinks; Security Command Center; Access Transparency; Assured Workloads; Sensitive Data Protection; Tokenisation and pseudonymisation; Threat modeling; Incident response; Compliance certifications
practice: quiz:A data scientist with legitimate read access; quiz:Which is true of Cloud Audit Logs; quiz:Which org policy constraint stops; quiz:Before sending customer complaint text; review:rev-genai-pilot
checkpoint: A data scientist has valid access to customer data. Name three separate controls that stop them copying it to a personal project, and say which one actually blocks it.

## Stage: Networking on Google Cloud
id: s4
summary: VPCs, private access to services, connecting to on-prem, and the front doors that let users in safely.

### Lesson: Your private network: VPC, subnets, firewalls, NAT
id: l12
minutes: 40
goal: A GCP **VPC** is global with regional **subnets**. **Firewall rules** sit at every VM's network interface, **Cloud NAT** gives outbound-only internet, and **Private Google Access** reaches Google APIs without it. These are the building blocks of every private workload.
concepts: Google's network, edge; VPC network; Subnet; Internal and external IP; VPC routes; VPC firewall rules; Cloud NGFW; Secure Tags vs; Cloud NAT; Private Google Access
practice: quiz:A VM with no external IP must download
checkpoint: Draw a VPC with two regions, private VMs, NAT and private API access, and label which pieces are global and which are regional.

### Lesson: Connecting networks and reaching services privately
id: l13
minutes: 40
goal: Real estates have many VPCs and many managed services. **Shared VPC** centralises the network, **peering** joins pairs (not transitively), **NCC** builds hubs, and **Private Service Connect** reaches services by private IP. IP planning keeps it all from colliding.
concepts: Private Service Connect; Private services access; Serverless VPC Access; VPC Network Peering; Shared VPC; Network Connectivity Center; IP address planning; Network egress costs; Network virtual appliances
practice: quiz:VPC A is peered with VPC B; diagram:hybrid-landing-zone
checkpoint: Explain why a bank's network team prefers Shared VPC to letting every team run its own VPC.

### Lesson: Hybrid connectivity and DNS
id: l14
minutes: 40
goal: Banks keep core systems on-prem, so cloud workloads need private, redundant links (**Interconnect**, **HA VPN**), dynamic routing (**Cloud Router**, BGP) and **hybrid DNS**, so names resolve to the private paths.
concepts: Cloud Router; Cloud VPN; Cloud Interconnect; Cloud DNS; Hybrid DNS
practice: journey:j-network; quiz:On-prem servers must call BigQuery privately; review:rev-network
checkpoint: Explain the three things that must all line up for an on-prem app to call Gemini privately.

### Lesson: Front doors and edge security
id: l15
minutes: 40
goal: Users reach services through **Cloud Load Balancing** at Google's edge, protected by **Cloud Armor**. Outbound traffic gets equally careful control with **Secure Web Proxy**. Network observability tools tell you why something can't connect.
concepts: Cloud Load Balancing family; Backend services and NEGs; Health checks; Traffic management on Application; Cloud CDN; Cloud Armor; Secure Web Proxy; VPC Flow Logs; Network Intelligence Center
practice: quiz:Users worldwide reach an HTTPS app; quiz:A TCP service must see the real client IP; quiz:Your load balancer marks every backend; quiz:Security requires that a private workload; journey:j-egress
checkpoint: Pick the right load balancer for (a) a global HTTPS app, (b) an internal service-to-service HTTP API, (c) a UDP service that needs client IPs, and justify each.

## Stage: Where code runs
id: s5
summary: Virtual machines, containers, Kubernetes and serverless, and how to choose between them.

### Lesson: Virtual machines and instance groups
id: l16
minutes: 35
goal: **Compute Engine** VMs give full control, and you pay for it in operations. **Managed instance groups** add autoscaling and self-healing, **Spot VMs** cut costs for interruptible work, and disks, images and snapshots handle state and recovery.
concepts: Virtualization and the hypervisor; Compute Engine; Machine families; Persistent Disk, Hyperdisk; Images, snapshots; Managed Instance Groups; Spot VMs; GPUs and TPUs; Autoscaling concepts; VM Manager
practice: quiz:Which workload is a poor fit for Spot VMs; diagram:three-tier-ha
checkpoint: Explain how a regional managed instance group keeps a web tier alive when a zone fails.

### Lesson: Containers and Kubernetes basics
id: l17
minutes: 45
goal: **Containers** package code with its dependencies so it runs the same everywhere. **Kubernetes** keeps the desired number of them running, connects them with **Services** and scales them. Learn the core objects first, then GKE will make sense.
concepts: Containers; Container images and registries; Kubernetes architecture; Pods, ReplicaSets; Kubernetes Services; Ingress and Gateway API; ConfigMaps and Kubernetes Secrets; Namespaces, resource requests; Probes; Autoscaling: HPA; StatefulSets, DaemonSets
practice: quiz:Your app's liveness probe checks the database
checkpoint: Explain how a request reaches a Pod in GKE, and what happens when that Pod dies.

### Lesson: GKE in practice and service mesh
id: l18
minutes: 30
goal: **GKE** runs Kubernetes for you (Autopilot even runs the nodes). A **service mesh** adds mTLS, traffic policy and telemetry between services. Stateless design and twelve-factor habits make all of it work.
concepts: GKE Standard vs Autopilot; GKE networking; Service mesh and sidecars; Stateless vs stateful services; Twelve-factor app
practice: quiz:GKE Pods need to read from Cloud Storage; diagram:gke-mesh-platform
checkpoint: When would you choose GKE Autopilot over Cloud Run, and what extra work do you take on?

### Lesson: Serverless with Cloud Run
id: l19
minutes: 35
goal: **Cloud Run** is the default home for new services: containers that scale to zero, with revisions, traffic splitting and service identity built in. Understand **concurrency** and **cold starts**, and you understand its costs and latency.
concepts: Serverless; Cloud Run services; Concurrency; Cold starts; Cloud Run jobs; Cloud Run functions
practice: quiz:A containerized REST API has unpredictable; quiz:A Cloud Run service calling an LLM spends
checkpoint: List four things you must design for when you put a service on Cloud Run (hint: the knock-on map in "How to architect").

## Stage: Where data lives
id: s6
summary: Storage types, database theory, GCP's databases and analytics, and how data moves between them.

### Lesson: Storage fundamentals and Cloud Storage
id: l20
minutes: 35
goal: Data comes as blocks, files or objects. **Cloud Storage** is the object store under almost everything (data lakes, documents for RAG, backups). Learn storage classes, lifecycle, signed URLs, and the difference between durability and having a backup.
concepts: Block vs file vs object; Cloud Storage (GCS); Storage classes; Object lifecycle management; Signed URLs; Filestore; Durability vs availability; Backup, PITR
practice: quiz:Which statement about Cloud Storage classes
checkpoint: Why isn't 11-nines durability a replacement for backups?

### Lesson: Database theory you'll use every day
id: l21
minutes: 45
goal: Every database is a set of trade-offs between **consistency**, **availability**, **latency** and **scale**. Transactions, isolation, replication and sharding explain why products behave as they do, and they let you predict bugs like stale reads.
concepts: OLTP vs OLAP; Row vs columnar; ACID transactions; Isolation levels; Consistency models; CAP theorem; Replication (sync vs async; Sharding and partitioning; Indexes
practice: quiz:After writing to Cloud SQL, users sometimes see
checkpoint: Explain synchronous vs asynchronous replication in terms of RPO and write latency.

### Lesson: Google Cloud's databases
id: l22
minutes: 45
goal: Now map the theory onto products: **Cloud SQL** and **AlloyDB** (relational, regional), **Spanner** (relational, global and strongly consistent), **Firestore** (documents), **Bigtable** (massive key/time-series), **Memorystore** (cache). Choosing well is mostly about access patterns and consistency needs.
concepts: Cloud SQL; AlloyDB for PostgreSQL; Spanner; Firestore; Bigtable; Memorystore; Caching patterns
practice: quiz:A global payments ledger needs; quiz:IoT devices write 500k readings; quiz:A team plans to put Cloud SQL HA
checkpoint: Choose a database for (a) a UK payments ledger, (b) per-card fraud features, (c) a mobile app's user profiles, and justify each.

### Lesson: Analytics, warehouses and governance
id: l23
minutes: 40
goal: **BigQuery** is GCP's analytics engine: serverless, columnar, priced by data scanned or by slots. Lakes, warehouses and lakehouses are ways of organising analytical data, and **Dataplex** gives the governance banks need (catalog, lineage, quality).
concepts: BigQuery; BigQuery partitioning and clustering; BigQuery slots; Data lake, data warehouse; Normalization, denormalization; Dataplex; Looker and Looker Studio
practice: quiz:A BigQuery table of 5 years of transactions; review:rev-analytics
checkpoint: Explain two ways to cut a BigQuery bill without losing any analysis.

### Lesson: Moving data: batch, streaming and CDC
id: l24
minutes: 45
goal: Data has to flow from systems of record to analytics and ML. **CDC** captures changes, **ETL/ELT** transforms them, **Dataflow** handles streams with event-time windows, and **Composer** orchestrates pipelines.
concepts: Batch vs streaming; ETL vs ELT; Change data capture; Data transfer and ingestion; Dataform; Dataflow and Apache Beam; Windowing, watermarks; Dataproc; Cloud Composer
practice: quiz:The analytics team wants near-real-time copies; journey:j-data; lab:lab-lakehouse
checkpoint: Trace a change in the core banking database to a dashboard number, naming each service and control on the way.

## Stage: How services talk
id: s7
summary: APIs, streaming responses, messaging, and the patterns that keep distributed systems correct when things fail.

### Lesson: APIs: REST, gRPC and good design
id: l25
minutes: 40
goal: Services talk **synchronously** (request/response) or **asynchronously** (events). For synchronous APIs you need the HTTP vocabulary (methods, status codes), API design habits, and when to choose **gRPC** over REST.
concepts: Synchronous vs asynchronous; Request/response vs event-driven; REST; HTTP methods: safety; HTTP status codes; API design; OpenAPI; gRPC and Protocol Buffers; GraphQL; Serialization formats; CORS
practice: quiz:Which is the best fit for an internal, high-throughput
checkpoint: Explain when to use gRPC and when REST, using one internal and one partner-facing example.

### Lesson: Real-time responses and API management
id: l26
minutes: 35
goal: LLM apps stream tokens (**SSE**), live UIs use **WebSockets**, and partners call back with **webhooks**. Once APIs leave your team, **API management** (**Apigee**) handles authentication, quotas, products and analytics.
concepts: WebSockets; Server-sent events; Long polling and webhooks; API gateway vs API management; Apigee; API Gateway and Cloud Endpoints; Service discovery
practice: quiz:Partners will consume your APIs; quiz:A chat UI streams LLM tokens; lab:lab-openapi
checkpoint: Why might a streaming chat answer appear all at once, and where would you look first?

### Lesson: Messaging and events
id: l27
minutes: 40
goal: **Pub/Sub** decouples services: publishers don't wait for consumers, and many consumers each get a copy. Delivery is **at-least-once**, which shapes everything downstream. **Eventarc**, **Cloud Tasks**, **Scheduler** and **Workflows** cover the other integration shapes.
concepts: Queue vs pub/sub; Pub/Sub; Delivery semantics; Message ordering; Dead-letter topics; Apache Kafka; Eventarc; Cloud Tasks; Cloud Scheduler; Workflows
practice: quiz:A legacy core-banking API can handle 50; quiz:When a new policy PDF lands; quiz:A message that always fails processing
checkpoint: Pub/Sub, Cloud Tasks or Workflows: give one bank example where each is the right choice.

### Lesson: Patterns that survive failure
id: l28
minutes: 45
goal: In distributed systems, networks fail and requests get retried. **Idempotency**, **timeouts**, **retries with backoff**, **circuit breakers**, the **outbox** and **sagas** are what stop a timeout turning into a double payment or an outage.
concepts: Idempotency and idempotency keys; Retries, exponential backoff; Timeouts, deadlines; Circuit breaker; Bulkheads, rate limiting; Backpressure and load shedding; Choreography vs orchestration; Saga pattern; Transactional outbox; Monolith vs microservices
practice: quiz:A payment API is called by a mobile app; quiz:Service A must update its database; journey:j-request; lab:lab-payments; review:rev-payments-ha
checkpoint: The app retried a payment after a timeout. Explain exactly how your design guarantees the customer is charged once.

## Stage: Running it reliably
id: s8
summary: Reliability targets, observability, safe delivery, governance and cost, and migrating what already exists.

### Lesson: Reliability targets and disaster recovery
id: l29
minutes: 40
goal: Reliability starts with targets: **SLOs** and **error budgets** for day-to-day, **RTO/RPO** for disasters. **High availability** handles zone loss automatically, while **DR** is a planned, tested procedure for losing a region.
concepts: Availability and "the nines"; SLI, SLO, SLA; Burn rate alerting; High availability vs disaster recovery; RTO and RPO; DR patterns; Redundancy and N+1; Graceful degradation
practice: quiz:Your SLO is 99.9% availability; quiz:RPO 0 and RTO under 5 minutes; journey:j-failure; review:rev-dr
checkpoint: Explain the difference between HA and DR using Cloud SQL as the example.

### Lesson: Observability and operations
id: l30
minutes: 40
goal: You can't run what you can't see. **Logs**, **metrics** and **traces** (with **OpenTelemetry**) explain what's happening. Alert on user-facing symptoms, run incidents calmly, and test capacity before your users do.
concepts: Observability vs monitoring; Cloud Logging; Structured logging; Cloud Monitoring; Distributed tracing; OpenTelemetry; Golden signals; Alerting practice; Incident management; Quotas, limits and capacity; Load testing and chaos
practice: quiz:Which alerting approach gives the fewest; quiz:An org has 300 projects; diagram:central-logging-secops
checkpoint: How would you find out which hop made one slow request slow, across 4 services and an LLM call?

### Lesson: Delivering change safely
id: l31
minutes: 45
goal: Production changes go through pipelines, not people: **CI/CD**, **infrastructure as code**, **canary** releases with automatic rollback, and supply-chain controls (**provenance**, **Binary Authorization**) that prove what's running.
concepts: CI/CD; Cloud Build; Cloud Deploy; Deployment strategies; Build-time vs runtime secrets; Environments and promotion; Testing types; Infrastructure as code; Terraform state; GitOps; Immutable infrastructure; Binary Authorization; Software supply chain; Vulnerability management
practice: quiz:A new release must reach 5% of users; quiz:You must prove that only images built; journey:j-deploy; review:rev-cicd
checkpoint: Describe the path of a code change to production and the evidence collected at each step.

### Lesson: Governance and cost
id: l32
minutes: 35
goal: Enterprises run on a **landing zone** (a governed foundation), on visibility (asset inventory, labels) and on **FinOps**. The **Well-Architected Framework** and **ADRs** are how designs are judged and recorded.
concepts: Landing zone and enterprise foundations; Labels; Cloud Asset Inventory; Billing export; Pricing models and discounts; FinOps; Rightsizing; CapEx vs OpEx; Active Assist; Google Cloud Well-Architected Framework; Architecture decision records
practice: quiz:A steady 24/7 baseline of 200 vCPUs
checkpoint: What are the six Well-Architected pillars, and which one does each of your last three lessons mostly serve?

### Lesson: Migration and hybrid
id: l33
minutes: 35
goal: Most bank work moves or wraps existing systems. The **7 Rs** frame the choice, **strangler fig** modernises gradually, and hybrid and multicloud need deliberate design, not accidents.
concepts: Migration strategies; Migration Center; Migrate to Virtual Machines; Database Migration Service; Strangler fig pattern; Anti-corruption layer; Wave planning; Licensing in the cloud; Hybrid cloud; Multicloud
practice: quiz:A VMware estate must exit; quiz:You're modernising a monolith; lab:lab-migrate
checkpoint: Explain why "lift and shift first, modernise later" is often right under a deadline, and what it costs.

## Stage: AI on Google Cloud
id: s9
summary: Classic ML, LLM fundamentals, RAG, agents, and how to make AI safe, governed and affordable.

### Lesson: Machine learning foundations
id: l34
minutes: 45
goal: Most production AI in banks is still classic ML (fraud, credit risk). Learn the **lifecycle**, **training vs inference**, how models are **evaluated**, and how they're **monitored** and governed once live.
concepts: AI vs ML; Learning types; ML lifecycle; Training vs inference; Model evaluation metrics; Choosing a model type; Feature engineering; Model registry; MLOps and pipelines; Model monitoring; Explainability; Accelerators and AI Hypercomputer
practice: quiz:A fraud model's precision is stable; journey:j-latency; lab:lab-fraud; diagram:credit-risk-mlops
checkpoint: Why is accuracy a bad metric for fraud detection, and what would you use instead?

### Lesson: LLM fundamentals on Agent Platform
id: l35
minutes: 40
goal: **Gemini Enterprise Agent Platform** (formerly Vertex AI) is where enterprise GenAI runs. Understand tokens, context windows and sampling, prompting and structured output, why models **hallucinate**, and when to prompt, retrieve or fine-tune.
concepts: Gemini Enterprise Agent Platform; Gemini, Gemma; AI Studio vs Agent Platform; Choosing a foundation model; LLM basics; Prompt engineering; Structured output; Hallucination; Fine-tuning vs RAG
practice: quiz:Which is a correct statement about choosing between AI Studio
checkpoint: A team wants to "fine-tune Gemini on our policies". Explain what you'd recommend instead, and why.

### Lesson: Retrieval-augmented generation
id: l36
minutes: 40
goal: RAG gives a model your current, private knowledge at question time: **embeddings**, **vector search**, **chunking** and **grounding** with citations. Most RAG failures are retrieval failures, so learn to see the whole pipeline.
concepts: Embeddings; Vector search; Retrieval-augmented generation; Chunking strategies; Grounding and citations; Document AI
practice: quiz:An internal assistant must answer from 20k; quiz:A RAG app's answers are often wrong; diagram:rag-policy-assistant; lab:lab-rag
checkpoint: Walk a question through a RAG system end to end, including where document permissions are enforced.

### Lesson: Agents, tools, MCP and A2A
id: l37
minutes: 45
goal: **Agents** loop through reasoning and **tool calls**. **ADK** builds them, **Agent Runtime** hosts them, **MCP** standardises tools and **A2A** connects agents to each other. Every tool is power, and every tool is risk.
concepts: Function calling and tool use; AI agents; Agent Development Kit; Agent Runtime; Sessions, state and memory; Model Context Protocol; Agent2Agent protocol; Human-in-the-loop
practice: quiz:What's the difference between MCP and A2A; quiz:Which set of metrics fits evaluating an agent; journey:j-agent; lab:lab-agent
checkpoint: Explain how an agent safely freezes a card: identity, tool design, confirmation and trace.

### Lesson: Safe, governed and affordable AI
id: l38
minutes: 45
goal: Production AI in a bank must resist **prompt injection**, keep customer data governed, prove quality with **evaluation**, and stay within quota, latency and cost budgets. This lesson ties AI to security and operations.
concepts: Prompt injection; Guardrails, safety filters; OWASP Top 10 for LLM; Data governance for GenAI; LLM and agent evaluation; Quotas, Provisioned Throughput; Token costs; Latency for LLM apps; Responsible AI
practice: quiz:An agent reads customer emails; quiz:Gemini calls from a batch job sometimes fail; review:rev-agent; diagram:private-gemini-onprem
checkpoint: List the layers of defence against indirect prompt injection in an agent that reads customer documents.

## Stage: The UK banking context
id: s10
summary: The regulation and risk vocabulary that shapes every bank design review.

### Lesson: Regulators, resilience and third parties
id: l39
minutes: 35
goal: The **PRA** and **FCA** set the rules that turn into requirements: **operational resilience** (impact tolerances), **outsourcing** and third-party risk (exit plans), and individual accountability. Learn to recognise which rules a design touches.
concepts: UK regulators; Three lines of defence; Operational resilience; Outsourcing and third-party risk; Critical Third Parties; Concentration risk; Senior Managers
practice: quiz:The business sets an impact tolerance of 30 minutes; quiz:What makes a cloud exit plan
checkpoint: Explain "impact tolerance" and why a component's SLA isn't evidence you meet it.

### Lesson: Data, models and customers
id: l40
minutes: 40
goal: **UK GDPR**, **DPIAs**, **data classification**, **model risk management** (SS1/23) and **Consumer Duty** shape every AI and data design. Learn what each asks of engineers.
concepts: UK GDPR; Data Protection Impact Assessment; Data classification; Record keeping; Customer data in LLM prompts; Model risk management; FCA Consumer Duty; AI regulation landscape; PCI DSS
practice: quiz:A team wants to use a SaaS AI tool; quiz:In a bank, which statement best describes PRA SS1; diagram:secure-data-science; review:rev-kyc
checkpoint: For an LLM that drafts customer complaint responses, list the regulatory questions a review board will ask.

## Stage: Think like an architect
id: s11
summary: Putting it all together: the design loop, end-to-end reasoning, worked designs and real case studies.

### Lesson: The design loop and the knock-on map
id: l41
minutes: 45
goal: You know the pieces. Architecture is combining them: understand, constrain, shape, decide, stress-test, communicate. Read the guide properly, especially the knock-on map, then design a full system.
concepts: Architecture decision records
practice: read:01; diagram:mobile-banking-api; diagram:open-banking; diagram:active-active-payments
checkpoint: Without notes, write out the 60-second checklist from the guide and apply it to a system you work on.

### Lesson: Worked designs and Google's case studies
id: l42
minutes: 60
goal: Watch a complete design done slowly (AI-assisted mortgage underwriting), then design Google's official case studies yourself before reading the analysis.
concepts: Google Cloud Well-Architected Framework
practice: read:03; diagram:kyc-onboarding; diagram:secure-cicd; diagram:agentic-servicing; diagram:realtime-fraud; diagram:cdc-lakehouse
checkpoint: Present one case-study design in 5 minutes: requirements → archetype → key decisions → trade-offs → failure walk.

### Lesson: Keep going: practice routine
id: l43
minutes: 20
goal: Skill comes from repetition with feedback. Set up the weekly routine: flashcards daily, labs and reviews twice a week, an Architecture Center kata weekly, a case study monthly.
concepts: Data mesh
practice: read:04; diagram:controlled-egress; diagram:three-tier-ha
checkpoint: Schedule your next four weeks of practice, and pick the first Architecture Center reference architecture for a kata.

# GCP on One Page

Re-read this every morning. By Friday you should be able to reproduce the 8 lenses and the service map from memory.

## 1. The skeleton: every solution is 8 lenses

Any system on any cloud can be broken down into these 8 parts. When you look at an architecture, label each box with a lens. When you design one, fill each lens in turn.

```
            ┌───────────────────────────────────────────────────────────┐
  WHO       │ 1. IDENTITY & ACCESS   who/what can do what, on which      │
            │                        resource (IAM, service accounts)    │
            ├───────────────────────────────────────────────────────────┤
  WHERE     │ 2. NETWORK             how bits get in, out, and between   │
            │                        (VPC, LB, DNS, NAT, hybrid links)   │
            ├──────────────────┬───────────────────┬────────────────────┤
  WHAT      │ 3. COMPUTE       │ 4. DATA           │ 5. INTEGRATION     │
            │ where code runs  │ where state lives │ how parts talk     │
            │ (Run, GKE, GCE)  │ (GCS, SQL, BQ…)   │ async (Pub/Sub…)   │
            ├──────────────────┴───────────────────┴────────────────────┤
  HOW WELL  │ 6. OPERATIONS          see it, deploy it, fix it           │
            │                        (Logging, Monitoring, CI/CD, IaC)   │
            │ 7. SECURITY            protect it beyond IAM               │
            │                        (secrets, KMS, perimeter, WAF)      │
            │ 8. COST                who pays, how much, how to shrink   │
            └───────────────────────────────────────────────────────────┘
  All of it sits inside:  Organization → Folders → Projects → Resources
```

## 2. The 9 facts that make GCP different

1. **The project is the unit of everything.** Billing, APIs, IAM and quotas attach to a project. Projects are free, so create plenty (per app per environment is normal).
2. **IAM is inherited downwards.** Grant at org/folder/project/resource and it flows down. Allow policies are additive. A grant higher up can't be revoked lower down (only *deny policies* can block it).
3. **VPC networks are global.** One VPC spans every region. **Subnets are regional.** (On AWS and Azure the network itself is regional.)
4. **Firewall rules belong to the VPC** and target instances by **network tag** or **service account**, not by attaching a group to a NIC.
5. **One anycast IP can serve the world.** The global external Application Load Balancer gives you one IP that routes users to the nearest healthy backend.
6. **Serverless first.** Cloud Run (containers), BigQuery (warehouse), Firestore and Pub/Sub have no servers or clusters to size.
7. **Workloads use service accounts, not keys.** Attach a service account to a VM, Cloud Run service or GKE workload and the client libraries pick it up automatically (Application Default Credentials). Downloaded JSON keys are a smell.
8. **Encrypted at rest by default.** Google-managed keys are the default. Use CMEK (Cloud KMS) when compliance needs you to own the key.
9. **Billing is per second, with automatic discounts.** Sustained-use discounts apply automatically. Committed-use discounts and Spot VMs are opt-in.

## 3. Location scope: memorize this table

| Scope | Examples | Implication |
|---|---|---|
| **Global** | VPC network, firewall rules, routes, global LB, IAM, Cloud DNS, images, snapshots, Pub/Sub topics | One definition works everywhere |
| **Multi-region** | Cloud Storage (US/EU/ASIA), BigQuery (US/EU), Spanner multi-region configs, Artifact Registry multi-region | Survives losing a whole region |
| **Regional** | Subnets, Cloud Run, Cloud SQL (HA), GKE regional cluster, regional MIG, regional persistent disk, Cloud NAT, Firestore (regional DB) | Survives losing a zone |
| **Zonal** | VM, zonal persistent disk, zonal MIG, zonal GKE cluster | **One zone fails, it fails.** Add redundancy yourself |

A **region** (for example `us-central1`) is a geographic area with 3 or more **zones** (`us-central1-a`, `-b`, `-c`). Zones are separate failure domains.

## 4. The service map (about 40 services that cover about 90% of real work)

Short descriptions. ★ = learn these well this week.

**Identity and access**
- ★ **IAM**: who (principal) can do what (role), on which resource
- ★ **Service accounts**: identities for workloads
- **Cloud Identity / Workspace**: the users and groups IAM refers to
- **Workload Identity Federation**: lets external workloads (GitHub Actions, AWS) use GCP without keys
- **Identity-Aware Proxy (IAP)**: identity-based access to apps and VMs, no VPN needed

**Network**
- ★ **VPC**: global private network
- ★ **Cloud Load Balancing**: one front door, global or regional
- **Cloud DNS**: managed authoritative DNS
- **Cloud CDN**: caches content at the edge
- **Cloud Armor**: WAF and DDoS protection at the LB
- **Cloud NAT**: outbound internet for private IPs
- **Cloud VPN / Interconnect**: links to on-prem or other clouds
- **Private Service Connect**: private endpoints to services
- **Shared VPC**: one network, many projects

**Compute** (the order runs from most control to least)
- **Compute Engine (GCE)**: VMs
- **Managed Instance Groups**: identical VMs with autoscaling and autohealing
- ★ **GKE (Standard/Autopilot)**: managed Kubernetes
- ★ **Cloud Run (services/jobs)**: containers, scale to zero
- **Cloud Run functions**: event-triggered snippets (formerly Cloud Functions)
- **App Engine**: legacy PaaS; prefer Cloud Run for new work
- **Batch**: batch jobs on VMs

**Data: storage and databases**
- ★ **Cloud Storage (GCS)**: object storage (blobs, files)
- **Persistent Disk / Hyperdisk**: block storage for VMs
- **Filestore**: managed NFS
- ★ **Cloud SQL**: managed MySQL/Postgres/SQL Server
- **AlloyDB**: high-performance PostgreSQL
- **Spanner**: global relational database with strong consistency
- ★ **Firestore**: serverless document database
- **Bigtable**: wide-column, huge throughput, low latency
- **Memorystore**: managed Redis/Valkey/Memcached

**Data: analytics**
- ★ **BigQuery**: serverless SQL data warehouse
- **Dataflow**: managed Apache Beam for stream and batch
- **Dataproc**: managed Spark/Hadoop clusters
- **Cloud Composer**: managed Airflow orchestration
- **Looker / Looker Studio**: BI and dashboards

**Integration**
- ★ **Pub/Sub**: global async messaging
- **Eventarc**: routes events to services
- **Cloud Scheduler**: managed cron
- **Cloud Tasks**: queue of HTTP tasks with rate limits
- **Workflows**: orchestrates API calls and steps
- **Apigee / API Gateway**: manage and secure APIs

**Operations**
- ★ **Cloud Logging**: collects and queries all logs
- ★ **Cloud Monitoring**: metrics, dashboards, alerts
- **Cloud Trace / Profiler**: latency and performance
- **Error Reporting**: groups app exceptions
- ★ **Cloud Build**: CI, builds containers
- ★ **Artifact Registry**: stores images and packages
- **Cloud Deploy**: CD pipelines to GKE and Run
- **Terraform / Infrastructure Manager**: infrastructure as code

**Security**
- ★ **Secret Manager**: stores API keys and passwords
- **Cloud KMS**: manages encryption keys
- **Organization Policy**: guardrails on what can be configured
- **VPC Service Controls**: data exfiltration perimeter
- **Security Command Center**: security posture and findings
- **Cloud Audit Logs**: who did what, when

**AI**
- **Gemini Enterprise Agent Platform** (renamed from Vertex AI in April 2026): build, tune and serve models
- **Gemini models on Agent Platform**: LLMs through an API
- **Agent Runtime** (formerly Agent Engine): managed runtime for agents (ADK and others)
- **Vector search** (Vector Search, AlloyDB/Cloud SQL pgvector, BigQuery vector search): similarity search for RAG

**Cost**
- ★ **Billing accounts, budgets and alerts**: who pays, and the early warning
- **Billing export to BigQuery**: analyze spend with SQL
- **Labels**: tag resources for cost allocation
- **Recommender**: rightsizing and idle-resource suggestions

## 5. Translation table (if you know another cloud)

| Concept | AWS | Azure | **GCP** |
|---|---|---|---|
| Account/billing boundary | Account | Subscription | **Project** (+ billing account) |
| Grouping | Organizations / OUs | Management groups | **Organization / Folders** |
| VMs | EC2 | Virtual Machines | **Compute Engine** |
| Autoscaling VM group | Auto Scaling Group | VM Scale Sets | **Managed Instance Group** |
| Kubernetes | EKS | AKS | **GKE** |
| Serverless containers | App Runner / Fargate | Container Apps | **Cloud Run** |
| Functions | Lambda | Functions | **Cloud Run functions** |
| Object storage | S3 | Blob Storage | **Cloud Storage** |
| Block / file | EBS / EFS | Managed Disks / Files | **Persistent Disk, Hyperdisk / Filestore** |
| Managed relational | RDS / Aurora | Azure SQL / PostgreSQL | **Cloud SQL / AlloyDB** |
| Global relational | Aurora DSQL (closest) | Cosmos DB (closest) | **Spanner** |
| Document / key-value | DynamoDB | Cosmos DB | **Firestore / Bigtable** |
| Cache | ElastiCache | Cache for Redis | **Memorystore** |
| Data warehouse | Redshift | Synapse / Fabric | **BigQuery** |
| Messaging | SNS + SQS / Kinesis | Service Bus / Event Hubs | **Pub/Sub** |
| Event routing | EventBridge | Event Grid | **Eventarc** |
| Orchestration | Step Functions | Logic Apps | **Workflows** |
| Network | VPC (regional) | VNet (regional) | **VPC (global)** |
| Load balancer | ALB / NLB / CloudFront | App Gateway / Front Door | **Cloud Load Balancing (+ CDN)** |
| DNS | Route 53 | Azure DNS | **Cloud DNS** |
| Private line | Direct Connect | ExpressRoute | **Cloud Interconnect** |
| WAF | AWS WAF / Shield | WAF / DDoS Protection | **Cloud Armor** |
| Secrets / keys | Secrets Manager / KMS | Key Vault | **Secret Manager / Cloud KMS** |
| Metrics / logs | CloudWatch | Azure Monitor | **Cloud Monitoring / Logging** |
| Audit trail | CloudTrail | Activity Log | **Cloud Audit Logs** |
| Container registry | ECR | ACR | **Artifact Registry** |
| CI/CD | CodeBuild / CodePipeline | Azure DevOps | **Cloud Build / Cloud Deploy** |
| IaC | CloudFormation | Bicep / ARM | **Terraform / Infrastructure Manager** |
| ML / GenAI | SageMaker / Bedrock | Azure ML / AI Foundry | **Gemini Enterprise Agent Platform (ex-Vertex AI)** |

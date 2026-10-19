# 11 · Migration, modernization and hybrid / multicloud

Most bank cloud work isn't greenfield. It's moving, wrapping or extending what already exists.

---

### Migration strategies (the "7 Rs")
`core` · Related: Migration Center, Strangler fig, TCO
**What:** **Rehost** ("lift and shift": move VMs as they are), **Replatform** ("lift and optimize": small changes such as moving to managed Cloud SQL or containers), **Refactor / re-architect** (redesign as cloud-native), **Repurchase** (move to SaaS), **Retire** (switch off), **Retain** (keep on-prem for now), **Relocate** (move a hypervisor estate wholesale, for example VMware → Google Cloud VMware Engine).
**How:** Choose per workload using business value, technical fit, risk, licensing, regulatory constraints and timelines. Most programmes combine several. Google's framing is **assess → plan → deploy → optimize**.
**Watch out:** Rehosting is fast but brings old problems with it, and VM costs can exceed on-prem without optimization.

### Migration Center (assess and plan)
`working` · Related: Migration strategies, TCO
**What:** Google's hub for discovering on-prem and other-cloud assets (through discovery clients or imports), mapping dependencies, producing TCO and rightsizing reports, and planning migration waves.

### Migrate to Virtual Machines
`working` · Related: Rehost, Compute Engine
**What:** A managed service that replicates VMs from VMware, AWS, Azure or physical servers into Compute Engine, with test clones, scheduled cut-over and rollback, using continuous block-level replication to minimize downtime.

### Database Migration Service (DMS)
`working` · Related: Cloud SQL, AlloyDB, Change data capture
**What:** Serverless database migrations with continuous replication (CDC) and minimal downtime: MySQL and PostgreSQL → Cloud SQL or AlloyDB, SQL Server → Cloud SQL, and **heterogeneous** Oracle or SQL Server → PostgreSQL / AlloyDB (with conversion workspaces, using Gemini to help convert schemas and code).

### Strangler fig pattern
`core` · Related: Monolith vs microservices, API gateway
**What:** Modernizing a legacy system incrementally. Put a facade (an API gateway or proxy) in front of it, then route individual capabilities one by one to new services until the old system can be retired. It avoids a risky "big bang" rewrite.
**GCP:** Apigee or a load balancer as the routing facade, new capabilities on Cloud Run or GKE, and CDC (Datastream) to keep the new data stores in sync during the transition. It's very common for mainframe and core-banking modernization.

### Anti-corruption layer
`working` · Related: Strangler fig, Domain-driven design
**What:** A translation layer between a new system and a legacy system with an awkward model, so the new code isn't shaped by legacy concepts (for example a service that converts mainframe COBOL copybook records into clean domain events).

### Wave planning, cut-over and rollback
`working` · Related: Migration strategies, DNS
**What:** Grouping workloads into **waves** by dependency and risk (pilot waves first), with rehearsed **cut-over runbooks** (freeze → final sync → switch DNS or traffic → validate) and defined **rollback** criteria and steps.
**Watch out:** Lower DNS TTLs in advance. Data synchronization in both directions makes rollback possible, and that matters most for payments.

### Licensing in the cloud
`working` · Related: Sole-tenant nodes, Bare Metal Solution
**What:** Commercial software licences (Windows Server, SQL Server, Oracle, RHEL, SAP) may be **pay-as-you-go** through Google images, or **BYOL** (bring your own licence). BYOL sometimes needs **sole-tenant nodes** (dedicated hosts) to meet per-core or per-socket terms. Oracle often lands on Bare Metal Solution or is migrated to PostgreSQL / AlloyDB.

### Hybrid cloud
`core` · Related: Cloud Interconnect, Hybrid DNS, Apigee hybrid
**What:** Running workloads across on-prem and public cloud as one estate, with private connectivity, shared identity, consistent security policy, hybrid DNS and often consistent platforms.
**GCP:** Interconnect or VPN + Cloud Router (network), Cloud Identity / Workforce Identity Federation (identity), **GKE Enterprise / GKE on bare metal or VMware** (consistent Kubernetes on-prem), **Apigee hybrid**, **AlloyDB Omni** and **Google Distributed Cloud** (Google Cloud services on-prem or air-gapped).
**Watch out:** It's typical for banks to keep core ledgers on-prem or on mainframe, with cloud for digital channels, analytics and AI. Latency and data-movement design across the hybrid boundary are central.

### Multicloud
`working` · Related: Cross-Cloud Interconnect, Exit strategy, Containers
**What:** Using more than one public cloud, either deliberately (best-of-breed services, concentration-risk reduction, regulatory exit planning) or through acquisitions and team choices.
**GCP:** Cross-Cloud Interconnect, HA VPN to AWS and Azure, BigQuery Omni (query data in AWS and Azure), GKE attached clusters (manage EKS and AKS as part of a fleet), Workload Identity Federation from AWS or Azure, and Terraform as a common IaC tool.
**Watch out:** Portability has a cost. Designing to the lowest common denominator throws away managed-service benefits. Regulators want a credible *exit plan*, not necessarily active multicloud.

### Mainframe modernization
`aware` · Related: Strangler fig, Change data capture
**What:** Strategies for COBOL and mainframe estates, which are very common in banking: offload data (CDC to BigQuery), wrap transactions with APIs (Apigee), refactor or rewrite with tooling (Google offers mainframe assessment, transpilation and Gemini-assisted code-understanding tools), or re-host on emulation. It's usually a long, phased programme.

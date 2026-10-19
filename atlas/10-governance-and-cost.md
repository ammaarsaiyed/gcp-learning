# 10 · Resource management, governance, architecture frameworks and cost

How a GCP estate is organized and governed, how architecture decisions are judged, and how money is spent and controlled.

---

### Resource hierarchy
`core` · Related: IAM policies and inheritance, Organization Policy, Landing zone
**What:** **Organization** (root, tied to a Cloud Identity / Workspace domain) → **Folders** (nestable, typically by business unit, environment or both) → **Projects** (the unit of billing, API enablement, quotas and most IAM) → **Resources**.
**How:** IAM policies, org policies, tags and some firewall policies inherit downwards. A project has an immutable, globally unique **project ID**, a mutable **name** and a Google-assigned **number**. Deleting a project shuts it down, and it can be restored within 30 days.
**GCP:** Bank layouts usually look like `org → {common/shared, prod, non-prod, sandbox} → business-unit folders → app/env projects`. Each design choice there changes which policies are easiest to apply.

### Landing zone and enterprise foundations
`core` · Related: Resource hierarchy, Shared VPC, Organization Policy
**What:** The pre-built, governed foundation that workloads land in: identity integration, hierarchy, org policies, networking (Shared VPC hubs, hybrid connectivity, DNS), centralized logging and monitoring, security tooling (SCC, KMS), billing setup, and a project factory (automated, compliant project creation).
**GCP:** Google's **enterprise foundations blueprint** and **Cloud Foundation Fabric FAST** are the reference implementations, deployed with Terraform. In a bank, the platform team owns it, and you mostly consume it, but you need to understand it to design within it.

### Project strategy
`working` · Related: Resource hierarchy, Environments
**What:** How workloads are split into projects. Common practice: **one project per application per environment** (for example `payments-api-dev` / `-prod`), plus shared projects (network host, logging, security, CI/CD, shared data).
**How:** Projects are free. They give isolation of IAM, quotas, billing and blast radius. Too few means shared permissions and noisy neighbours. Too many needs automation (a project factory) and consistent naming and labels.

### Labels
`working` · Related: Secure Tags vs network tags vs labels, Billing export
**What:** Key/value metadata on most resources (`env=prod`, `team=fraud`, `cost-centre=1234`, `data-class=confidential`), used for filtering, automation and **cost allocation** (labels appear in billing exports). Labels have no security effect.

### Cloud Asset Inventory
`working` · Related: Security Command Center, Policy Analyzer
**What:** A searchable inventory of all resources and IAM policies across the org, with a **history** of changes (about 35 days), real-time **feeds** to Pub/Sub, and **exports** to BigQuery for analysis ("every bucket without CMEK", "every service account with Owner").

### Quotas and limits
`core` · Related: Capacity planning, Gemini quotas
**What:** Per-project or per-region caps on resources (CPUs, IPs, GPUs) and API rates (requests per minute, tokens per minute). They protect both Google's capacity and you (from runaway spend or a bug). Most can be increased by request. **Quota adjuster** can automate increases. You can also *lower* quotas yourself as a cost guardrail (for example capping BigQuery bytes scanned per day).

### Billing accounts and billing structure
`core` · Related: Budgets, Billing export
**What:** A **Cloud Billing account** pays for one or more linked projects. It can be self-serve (card) or invoiced. Subaccounts are for resellers. Billing IAM roles are separate from project roles (Billing Account Administrator, User, Viewer).
**How:** Unlinking billing stops paid services in the project. Only principals with Billing Account User on the account can link projects to it.

### Budgets and alerts
`core` · Related: Billing accounts, Pub/Sub
**What:** Thresholds on actual or forecasted spend for a billing account, filtered by projects, services or labels, that **notify** by email or publish to **Pub/Sub** (for automated responses).
**Watch out:** Budgets don't cap spend. A hard stop needs automation (Pub/Sub → a function that disables billing or scales services down). Quotas are the other preventive control.

### Billing export to BigQuery and FinOps reporting
`working` · Related: Labels, FinOps
**What:** Detailed usage-cost data (standard and detailed, resource-level), pricing data, and committed-use data exported daily to BigQuery for SQL analysis, Looker dashboards, showback and chargeback by labels, and anomaly detection.

### Pricing models and discounts
`core` · Related: Spot VMs, BigQuery slots, Provisioned Throughput
**What:** **On-demand / pay-as-you-go**: per second or per unit, no commitment. **Sustained use discounts (SUDs):** automatic discounts for VMs that run a large part of the month (some machine families). **Committed use discounts (CUDs):** a 1- or 3-year commitment for big discounts. *Resource-based* CUDs commit to vCPU and memory in a region. *Spend-based (flexible)* CUDs commit to a $/hour of spend across services. **Spot VMs:** deep discounts for interruptible capacity. **BigQuery editions** commitments. **Provisioned Throughput** for Gemini (reserved model capacity).
**Watch out:** Commit only to steady baseline usage. Cover spiky usage with on-demand or Spot.

### FinOps
`working` · Related: Billing export, Labels, Rightsizing
**What:** The practice of cloud financial management: shared accountability between engineering, finance and product. The phases are **Inform** (visibility, allocation, showback or chargeback), **Optimize** (rightsizing, discounts, waste removal) and **Operate** (governance, budgets, continuous improvement).
**GCP:** Labels and tags + billing export + Looker dashboards + recommenders + budgets + CUD management. For AI workloads, track **cost per request and per token per use case**.

### Rightsizing and waste reduction
`working` · Related: Active Assist, Autoscaling
**What:** Matching resources to real usage: downsize over-provisioned VMs, delete idle disks, IPs and snapshots, scale to zero where possible, use autoscaling, apply lifecycle policies to storage, set GKE requests correctly, tune BigQuery queries, and stop non-prod environments out of hours.

### CapEx vs OpEx and TCO
`working` · Related: Migration, Pricing models
**What:** **CapEx:** upfront capital spend on assets (servers, data centres), depreciated over years. **OpEx:** ongoing operating spend (cloud consumption). **TCO** (total cost of ownership) compares *everything*: hardware, licences, power and cooling, facilities, staff, downtime and opportunity cost, not just the hosting price.
**Watch out:** Cloud moves spend from CapEx to OpEx and makes it variable. That's great for agility, but it needs FinOps discipline.

### Regions, zones and choosing a location
`core` · Related: Failure domains, Data residency, Latency
**What:** Choose a region based on: (1) **regulatory and residency** requirements, (2) **latency** to users and systems (including on-prem Interconnect locations), (3) **service and machine availability** (not every product, model or GPU exists in every region), (4) **price** (it varies by region), (5) **sustainability** (carbon-free energy percentage).
**GCP:** For UK banks, `europe-west2` (London) is the default. Check every service's availability there, including AI model availability and **ML processing location**, before committing to a design.

### Google Cloud Well-Architected Framework
`core` · Related: Solution design, Trade-offs
**What:** Google's best-practice framework for designing and operating workloads. **Pillars:** **operational excellence**, **security, privacy and compliance**, **reliability**, **cost optimization**, **performance optimization**, **sustainability**. There are also **perspectives** that apply the pillars to specific contexts (for example **AI and ML**, and **financial services**).
**How:** Use the pillars as a review checklist for any design, and record trade-offs explicitly (for example "multi-region active-active improves reliability but doubles cost and adds consistency complexity").
**GCP:** The Professional Cloud Architect exam treats it as foundational. Bank architecture review boards ask essentially the same questions.

### Architecture decision records (ADRs) and trade-offs
`working` · Related: Well-Architected Framework
**What:** Short documents recording a significant decision: context, options considered, the decision, consequences and trade-offs. They make the reasoning reviewable and stop old debates from restarting.
**Watch out:** The most valuable skill in design reviews isn't knowing every product. It's stating what each option *gives up*.

### Sustainability
`aware` · Related: Well-Architected Framework, Regions
**What:** Google publishes a carbon-free energy percentage per region, and offers the **Carbon Footprint** report (emissions by project, service and region; exportable to BigQuery). Region choice, utilization and rightsizing are the main levers. It increasingly appears in bank ESG reporting.

### Support and service health
`aware` · Related: Incident management
**What:** Google Cloud support tiers (Standard, Enhanced, Premium with a Technical Account Manager), **Personalized Service Health** (incidents affecting *your* projects, with alerts and APIs), and the public status dashboard. Regulated firms typically need Premium support to meet incident-response obligations, and some features (Access Approval and others) depend on it.

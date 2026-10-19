# 13 · UK banking regulation, risk and controls (for cloud and AI engineers)

You don't need to be a lawyer. You do need to recognize which rules a design touches, use the right words in design reviews, and know which controls answer which concern. This is an engineer's map, not legal advice: your bank's second line (risk, compliance, legal, the data protection officer) interprets the details, and rules change, so check current versions.

---

### UK regulators and who cares about what
`core` · Related: Operational resilience, Model risk management, UK GDPR
**What:** **PRA** (Prudential Regulation Authority, part of the Bank of England): safety and soundness of banks (capital, liquidity, operational resilience, outsourcing, model risk). **FCA** (Financial Conduct Authority): conduct and consumer outcomes, market integrity (Consumer Duty, fair treatment, financial crime systems). Large banks are **dual-regulated**. **Bank of England** also oversees financial market infrastructures and, with PRA and FCA, critical third parties. **ICO** (Information Commissioner's Office): data protection (UK GDPR). **PSR** (Payment Systems Regulator): payments.
**Watch out:** In design reviews, "is this material outsourcing?", "which important business service does it support?", "is this a model under our MRM policy?" and "have we done a DPIA?" are the questions that most often stop a launch.

### Three lines of defence
`working` · Related: Model risk management, Separation of duties
**What:** The standard risk-governance model. **1st line:** the business and technology teams that own and manage risks (you, building systems with controls). **2nd line:** independent risk and compliance functions that set policy and challenge the first line (operational risk, model risk, information security risk, data protection). **3rd line:** internal audit, giving independent assurance.
**Why it matters:** Your designs are reviewed by the 2nd line and audited by the 3rd. Evidence (logs, tests, approvals, IaC history) is how controls get proven.

### Operational resilience (PRA SS1/21, FCA PS21/3)
`core` · Related: RTO and RPO, Disaster recovery, Chaos engineering
**What:** The UK framework requiring firms to identify **important business services** (IBS: services whose disruption could harm customers or market integrity, or threaten the firm's safety; for example making payments, accessing accounts), set an **impact tolerance** for each (the maximum tolerable disruption, usually a time limit), **map** the people, processes, technology, facilities and third parties behind each service, and **test** that they can stay within tolerance under **severe but plausible** scenarios. Firms had to be able to remain within tolerances by **31 March 2025**, and now must sustain and evidence it.
**How:** For engineers this means: know which IBS your system supports, design RTO and RPO and DR so the *end-to-end service* stays inside its impact tolerance, include cloud regions, zones, providers and SaaS dependencies in the mapping, and run and document DR and failover tests.
**Watch out:** Impact tolerances are about **the business service end to end**, not one component's SLA. A 99.99% database doesn't help if the identity provider is a single point of failure.

### Outsourcing and third-party risk (PRA SS2/21)
`core` · Related: Critical third parties, Exit strategy, Shared responsibility model
**What:** PRA expectations for outsourcing and third-party arrangements, explicitly including cloud. Key elements: **materiality assessment**, **due diligence**, contractual requirements (**access, audit and information rights** for the firm and the regulator, sub-outsourcing controls, data security and location), **data security** (classification, encryption, key management, location), **business continuity**, **concentration risk**, and **exit planning**: documented plans for both a planned (non-stressed) exit and a **stressed exit** (the provider fails or terminates suddenly), with testing where appropriate. Firms must notify the PRA of material outsourcing.
**GCP:** The controls that answer it: data location (org policies), CMEK/EKM, Access Transparency and Access Approval, audit logs, Google's audit reports and contractual financial-services addenda, multi-region DR, and portability through containers, open formats and Terraform.

### Critical Third Parties (CTP) regime
`working` · Related: Outsourcing (SS2/21), Concentration risk
**What:** Under the Financial Services and Markets Act 2023, **HM Treasury** can designate third parties (for example major cloud providers) whose failure could threaten UK financial stability as **critical third parties**. The regulators (PRA, FCA, Bank of England) then oversee them *directly* against fundamental rules and operational risk and resilience requirements (rules in force from January 2025).
**Watch out:** Designation doesn't remove a firm's own responsibility for managing its third-party risk. You still need your own resilience and exit plans.

### Concentration risk and cloud exit strategy
`working` · Related: Outsourcing (SS2/21), Multicloud, Containers
**What:** **Concentration risk:** too much critical activity relying on one provider (at firm level and across the sector). **Exit strategy:** a credible, tested plan to move services away from a provider, or bring them back in-house, within a reasonable time, in both stressed and planned scenarios.
**How:** Engineering levers that make exit credible: containers and Kubernetes, open data formats (Parquet, Iceberg, Avro), open-source-compatible databases (PostgreSQL), infrastructure as code, abstraction of model providers behind a gateway (for AI: being able to switch between Gemini, Claude and open models), documented data export paths, and avoiding unnecessary proprietary dependencies in the *most critical* services.
**Watch out:** Regulators want a *proportionate and credible* plan, not necessarily active multicloud. Over-engineering for portability has its own cost and risk.

### UK GDPR and the Data Protection Act 2018
`core` · Related: Data residency, Sensitive Data Protection, DPIA
**What:** The UK's data protection law. Core principles: lawfulness, fairness and transparency, **purpose limitation**, **data minimisation**, accuracy, **storage limitation**, integrity and confidentiality (security), and **accountability**. Data subject rights: access, rectification, **erasure**, restriction, portability, objection, and rights around **automated decision-making** (UK GDPR Article 22, as amended by the Data (Use and Access) Act 2025; check current rules). **International transfers** outside the UK need adequacy regulations or safeguards (for example the UK IDTA or the Addendum to EU SCCs). **Breach notification** to the ICO within **72 hours** where required.
**How:** Engineering implications: know where personal data lives (including logs, prompts, embeddings, agent memory and backups), minimise what goes into models, enforce retention, support deletion (crypto-shredding helps with backups), control transfers (region choice, global AI endpoints), and keep processing records.

### Data Protection Impact Assessment (DPIA)
`working` · Related: UK GDPR, Responsible AI
**What:** A required assessment before processing that's likely to be high-risk to individuals: new technologies, large-scale profiling, automated decisions with significant effects. **Most customer-data AI and GenAI use cases need one.** It records purposes, necessity, risks and mitigations, and the data protection officer reviews it.

### Model risk management (PRA SS1/23)
`core` · Related: Model registry, LLM evaluation, Explainability
**What:** The PRA's **Model Risk Management principles for banks** (in effect since May 2024) set expectations for identifying and managing model risk, in five principles: (1) **model identification and classification** (a firm-wide **model inventory** and risk **tiering**), (2) **governance** (board oversight, an accountable SMF, policies), (3) **model development, implementation and use** (data quality, testing, documentation), (4) **independent model validation** (including ongoing performance monitoring), (5) **model risk mitigants** (for example restrictions, overrides, post-model adjustments). It applies directly to banks with internal-model approval for regulatory capital, and is widely adopted as good practice by others. It explicitly covers AI and ML models and model complexity.
**How:** For GenAI and agents, expect: inventory entries for each use case (model + prompts + retrieval + tools as a system), tiering by impact, documented evaluation and validation evidence, monitoring of performance and drift, change control for prompt, model-version and tool changes, and fallback plans.

### FCA Consumer Duty
`working` · Related: Responsible AI, Explainability, Human-in-the-loop
**What:** FCA rules (from July 2023) requiring firms to **deliver good outcomes for retail customers**: products and services fit for purpose, fair price and value, **consumer understanding** (clear communications), **consumer support** (no unreasonable barriers), and attention to **vulnerable customers**. Firms must monitor and evidence outcomes.
**Why it matters:** Customer-facing AI (chatbots, decisions, personalized communications) must produce outcomes that are accurate, fair, understandable and easy to escalate to a human. Poor AI outcomes are a conduct risk.

### Senior Managers and Certification Regime (SM&CR)
`working` · Related: Model risk management, Three lines of defence
**What:** Individual accountability: named **Senior Management Function** holders are personally responsible for areas of the business (including technology, operations and, in practice, AI use and model risk). That's why governance sign-off on cloud and AI systems is taken seriously and documented carefully.

### AI regulation landscape (UK and EU)
`working` · Related: Model risk management, Consumer Duty, Responsible AI
**What:** **UK:** a principles-based, regulator-led approach (safety, transparency, fairness, accountability, contestability), applied through existing rules (Consumer Duty, SM&CR, SS1/23, UK GDPR, equality law). The FCA and the Bank of England run AI initiatives (for example supervised AI testing). **EU AI Act:** risk-based regulation with obligations phasing in. **Creditworthiness assessment and credit scoring of individuals is "high-risk"**. It matters for UK banks with EU operations or EU customers. Timelines have been subject to change, so check them.
**Watch out:** Bank internal AI policies often go further than law: approved-model lists, use-case risk tiering, mandatory evaluation, human oversight rules, bans on certain data in prompts.

### DORA (EU Digital Operational Resilience Act)
`aware` · Related: Operational resilience, Outsourcing
**What:** EU regulation (applying from January 2025) on ICT risk management, incident reporting, resilience testing (including threat-led pen testing), and ICT third-party risk for **EU** financial entities. It affects UK groups with EU-regulated subsidiaries and is conceptually similar to the UK framework.

### PCI DSS
`working` · Related: Tokenisation, Network segmentation, Cloud HSM
**What:** The Payment Card Industry Data Security Standard (v4.x) for anyone storing, processing or transmitting cardholder data: network segmentation, encryption, key management, access control, logging and monitoring, vulnerability management, regular testing.
**How:** The biggest lever is **scope reduction**: tokenize card numbers early so most systems never see them, and isolate the cardholder data environment (separate projects, VPC-SC, strict firewalls). Google Cloud is a PCI DSS-validated provider for in-scope services, and you're responsible for your part.

### BCBS 239 (risk data aggregation and reporting)
`aware` · Related: Dataplex, Data quality
**What:** Basel Committee principles for risk data: accuracy, integrity, completeness, timeliness and adaptability of risk data aggregation and reporting, with strong data governance and architecture. In practice: lineage, data quality controls, reconciliation, and clear data ownership for regulatory reporting pipelines.

### Record keeping, audit trails and retention
`working` · Related: Cloud Audit Logs, Bucket lock, Log sinks
**What:** Regulators expect firms to keep records (communications, transactions, decisions, system changes) for defined periods, often 5–7+ years depending on the rule, in a form that can't be altered undetected, and to retrieve them on request.
**GCP:** Locked log buckets and retention, Cloud Storage **bucket lock / retention policies** (WORM), BigQuery with controlled access, CMEK, centralized logging projects, IaC history in git, and Cloud Deploy and Cloud Build audit trails. For AI: retain prompts, responses, model versions and retrieved sources where they support decisions or customer communications (and balance that against data minimisation).

### Data classification
`working` · Related: Sensitive Data Protection, Organization Policy, VPC Service Controls
**What:** Labelling data by sensitivity (for example Public / Internal / Confidential / Highly Confidential or Restricted), with each class mapped to required controls: encryption and key type, location, access approval, logging, whether it may be used in AI prompts, whether it may leave the perimeter.
**GCP:** Implemented through project and dataset segregation, Sensitive Data Protection discovery, Dataplex and BigQuery policy tags, labels and tags, VPC-SC perimeters per classification, and org policies.

### Customer data in LLM prompts
`core` · Related: Data governance for GenAI, Sensitive Data Protection, DPIA
**What:** The practical question behind most bank GenAI reviews: "what personal or confidential data reaches the model, where is it processed, is it stored, and who can see it?"
**How:** A typical control set: an approved enterprise platform only (Agent Platform with the right terms), regional processing where required, VPC-SC + private connectivity, **PII minimisation and redaction** before prompting (Sensitive Data Protection, Model Armor), no customer data in model training without explicit approval, controlled prompt and response logging (with retention limits and access controls), a DPIA, model-risk inventory and evaluation, human review for customer-impacting outputs.

### Fraud, AML and financial crime systems
`aware` · Related: Bigtable, Dataflow, Model monitoring
**What:** High-volume, low-latency ML (transaction fraud scoring, mule detection, AML transaction monitoring, sanctions screening) with strict explainability, auditability and tuning governance. GenAI increasingly assists investigators (case summaries, SAR narrative drafting) with human review.
**GCP:** Streaming features (Pub/Sub → Dataflow → Bigtable or Feature Store), models served on endpoints, BigQuery for investigation analytics. Google also offers an **AML AI** product for transaction monitoring.

### Open Banking and FAPI
`aware` · Related: OAuth 2.0, mTLS, Apigee
**What:** UK Open Banking (from the CMA order and PSD2) requires standardized, secure APIs letting authorized third parties access account data and initiate payments with customer consent. It uses the **FAPI** (Financial-grade API) security profile: OAuth 2.0 / OIDC hardened with **mTLS** or private-key JWT client authentication, signed request objects, and certificate-bound tokens.
**GCP:** Apigee (with mTLS on the load balancer and OAuth/FAPI policies) is a common platform for these APIs.

### CBEST and threat-led penetration testing
`aware` · Related: Penetration testing, Operational resilience
**What:** The Bank of England's intelligence-led red-teaming framework for systemically important firms. Real-world threat actors' tactics are simulated against live production systems, which can include cloud environments and identities.

# Practice resources (and how to use each one)

There's a lot of material online. Most of it is useful only if you use it **actively**: design first, then compare. Here are the sources worth your time, and the exercise that turns each into practice.

## Google Cloud (official)

| Resource | What it is | How to practise with it |
|---|---|---|
| [Cloud Architecture Center](https://docs.cloud.google.com/architecture) | Hundreds of reference architectures, design guides and deployable solutions | **Reverse-engineer kata:** read only a guide's problem statement or first paragraph, design it yourself in 20 minutes, then compare with Google's diagram. Note every difference and why they chose differently |
| [Architecture fundamentals](https://docs.cloud.google.com/architecture/fundamentals): Enterprise foundations blueprint, landing zone design, **deployment archetypes** | How enterprise GCP estates are structured (what your bank's platform team built) | Map your bank's real landing zone to the blueprint: hierarchy, network, identity, logging. Where does it differ, and why? |
| [Well-Architected Framework](https://docs.cloud.google.com/architecture/framework) | Pillars: operational excellence, security, reliability, cost, performance, sustainability, plus perspectives | Score one of your designs against each pillar's recommendations. Write down 3 gaps |
| [Financial services perspective](https://docs.cloud.google.com/architecture/framework/perspectives/fsi) | WAF applied to banks, payments, insurers and markets (resilience, security, regulatory angles) | Read before any bank design review. Turn each recommendation into a review question |
| [Generative AI architectures overview](https://docs.cloud.google.com/architecture/genai-overview) | RAG (several vector-store variants, GraphRAG), agentic RAG, single- and multi-agent systems with ADK and MCP, secure networking for RAG, CI/CD for RAG | Compare each with the [RAG lab](../practice/design-lab.md) and the [agent lab](../practice/design-lab.md). Which choices differ, and when would you pick theirs? |
| [Architecture Center release notes](https://docs.cloud.google.com/architecture/release-notes) | What's new (new agent and AI reference architectures appear here first) | Skim monthly. Pick one new architecture a month for a kata |
| [PCA exam guide](https://services.google.com/fh/files/misc/v6.1_pca_professional_cloud_architect_exam_guide_english.pdf) + case studies ([EHR](https://services.google.com/fh/files/misc/v6.1_pca_ehr_healthcare_case_study_english.pdf), [Cymbal](https://services.google.com/fh/files/misc/v6.1_pca_cymbal_retail_case_study_english.pdf), [KnightMotives](https://services.google.com/fh/files/misc/v6.1_pca_knightmotives_automotive_case_study_english.pdf), [Altostrat](https://services.google.com/fh/files/misc/v6.1_pca_altostrat_media_case_study_english.pdf)) | The syllabus for architects, and four realistic businesses | Design each case from scratch before reading [the analysis](03-worked-designs-and-case-studies.md). Redo one a month with a twist (a new region, a new regulation, 10× traffic) |
| [Architecture diagramming tool](https://googlecloudcheatsheet.withgoogle.com/architecture) | Free drag-and-drop GCP diagrams with templates, linked to product descriptions | Draw every design you practise. Drawing exposes missing pieces |
| [Google Cloud Skills Boost](https://www.cloudskillsboost.google) | Hands-on labs in temporary projects, including challenge labs | When you have time to build, choose **challenge labs** (no instructions) on networking, security and AI. They test integration, not following steps |
| [Google SRE books](https://sre.google/books/) (free online) | How Google runs production: SLOs, alerting, incident response, release engineering | Read the chapters on SLOs, alerting on SLOs and handling overload. Then rewrite the alerting for one of your services |

## Banking and AI governance (very relevant to you)

| Resource | What it is | How to practise |
|---|---|---|
| [FINOS Common Cloud Controls](https://github.com/finos/common-cloud-controls) | An open standard of cloud controls for financial services, started by Citi with major banks and cloud providers (Google among them) | Pick a service (for example object storage) and map each CCC control to the GCP feature that implements it. That's exactly what bank cloud security teams do |
| [FINOS AI Governance Framework](https://air-governance-framework.finos.org/) | An open catalogue of AI risks and mitigations for financial institutions, including agentic AI risks (prompt injection, memory poisoning, agent authority), mapped to OWASP, the EU AI Act, Consumer Duty and others | For each AI design you make, pick the relevant risks and name the control in your architecture. Great preparation for model risk and security reviews |
| [OWASP GenAI Security Project / Top 10 for LLM apps](https://genai.owasp.org/) | Security risks for LLM and agent applications | Threat-model one of the [design lab](../practice/design-lab.md) agents against all ten |
| Bank of England / PRA and FCA publications: **SS1/21** (operational resilience), **SS2/21** (outsourcing and third-party risk), **SS1/23** (model risk management), **Consumer Duty** | The actual rules behind most bank design reviews | Read the executive summaries. Then, for one of your systems, write the "impact tolerance + mapping + testing" paragraph and the "model risk tier + validation" paragraph |

## General architecture skill (cloud-agnostic)

| Resource | What it is | How to practise |
|---|---|---|
| [System Design Primer](https://github.com/donnemartin/system-design-primer) | A well-known open guide to scalability, caching, consistency, load balancing and databases, with worked designs | Do its exercises, then translate each design into GCP services. That forces you to connect generic concepts to products |
| *Designing Data-Intensive Applications* (Martin Kleppmann) | The best book on data systems: replication, partitioning, transactions, consistency, streams | Read chapters 5–9 alongside atlas [06](../atlas/06-storage-and-databases.md) and [07](../atlas/07-data-processing-and-messaging.md). It explains *why* Spanner, Bigtable and Pub/Sub behave as they do |
| [C4 model](https://c4model.com/) | A simple, layered way to draw architecture (context → containers → components) | Redraw one of your team's diagrams as C4 context and container diagrams |
| [Architecture decision records](https://adr.github.io/) | Templates and practice for recording decisions | Write ADRs for the 3 biggest decisions in your current project |
| Architectural katas (Neal Ford's kata format) | Short, realistic briefs designed in small groups, then presented and critiqued | Run one with colleagues every couple of weeks using the [design lab](../practice/design-lab.md) briefs or your own |
| [Cloud Resume Challenge](https://cloudresumechallenge.dev/) | A single end-to-end project (with a GCP edition) that touches DNS, CDN, serverless, a database, IaC and CI/CD | When you're ready to build, it's the best "everything together" project |

## A sustainable practice routine (about 2 hours a week)

| Cadence | Activity |
|---|---|
| Daily, 10 min | Flashcards that are due, in the app |
| Twice a week, 20 min | One [design lab](../app/index.html#architect) scenario or one [design review](../practice/design-reviews.md) |
| Weekly, 45 min | **Kata:** one Architecture Center reference architecture. Design from the problem statement, then compare |
| Fortnightly, 30 min | Walk one [journey](02-end-to-end-journeys.md) aloud, then write one for a system at work |
| Monthly, 1 h | One PCA case study with a twist, or write a case study of a real work system |
| Every real design at work | The [60-second checklist](01-how-to-architect.md#10-a-60-second-mental-checklist-memorise-this) + the knock-on map before the review |

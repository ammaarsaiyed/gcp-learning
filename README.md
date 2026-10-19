# GCP in 5 Days, with depth

A focused but complete way to learn Google Cloud for someone who learns on the job, is an **AI engineer in a UK bank**, and has bounced off the 72-hour learning paths.

**Goal:** by Friday you can (1) explain the building blocks and the networking, security and distributed-systems ideas underneath them, (2) look at any architecture and name every part and why it's there, and (3) design solutions and defend the trade-offs in a bank's architecture review.

## What's in here

| Part | What it is | Use it for |
|---|---|---|
| [**How to architect**](guide/01-how-to-architect.md) · [**Journeys**](guide/02-end-to-end-journeys.md) · [**Worked designs and case studies**](guide/03-worked-designs-and-case-studies.md) · [**Practice resources**](guide/04-practice-resources.md) | Reading on **putting the pieces together**: the design loop, the "if you choose X you must handle Y" knock-on map, failure walks, the questions a bank review board asks, 9 end-to-end journeys (request, identity, data, deployment, failure, agent, network, latency, egress), a full worked AI-underwriting design, Google's 4 official architect case studies analysed, and curated online practice | **Integration, the most important part.** Read 01 first |
| **Architect section of the app** | Journeys you step through on highlighted diagrams, a **design lab** (7 briefs, 58 decisions with graded feedback and requirement twists, plus your design and a reference design built as you go), and **design reviews** (8 flawed proposals: find the real problems, ignore the red herrings) | Practising architecture interactively |
| [**Concept atlas**](atlas/README.md) | 401 concepts in 13 domains, from TCP handshakes to PRA SS1/23. Each has *What*, *How it works*, *On GCP* and *Watch out*, at three tiers (core / working / aware). | **Depth and completeness.** This is the map of what matters. |
| [**Practice app**](app/index.html) | An interactive page: rate yourself on every concept, spaced-repetition flashcards, **18 architecture diagrams with hidden labels** to name, 63 scenario questions, and a progress view showing your gaps. | **Active recall.** It replaces re-reading and re-watching. |
| [**Architecture library**](practice/architectures.md) | The same 18 designs as text: each component, and why it was chosen. Most are bank or AI scenarios (RAG assistant, fraud scoring, agentic servicing with MCP/A2A, Open Banking, VPC-SC data science, hybrid landing zone…). | Learning to *see* solutions. |
| [`flashcards.csv`](flashcards.csv) | Every atlas concept plus the original 95 cards, ready to import into Anki. | Spaced repetition on your phone. |
| [One-pager](00-gcp-on-one-page.md) and [cheat sheets](cheatsheets/) | The skeleton (the 8 lenses), the service map, decision trees, the design template, `gcloud` grammar. | Morning review, and reference while designing. |
| [Hands-on labs](day-1-foundations.md) (`day-*.md`) | Optional. A Cloud Run app that grows through the week. | Later, when you have time to build. |

### How do you know nothing important is missing?

The things you listed (perimeters, gRPC, ingress/egress, Apigee, ports, handshakes) were examples. The real risk is everything you *don't* know to ask about. So the atlas isn't a list of topics I picked. It was built bottom-up and then checked:

1. **Layered from fundamentals up:** networking basics → GCP networking → identity → security and cryptography → compute → data theory and storage → data pipelines → APIs and distributed-systems patterns → reliability and operations → governance and cost → migration and hybrid → AI/ML/agents → UK banking regulation.
2. **Cross-checked against Google's official exam guides** (current versions): Associate Cloud Engineer, Professional Cloud Architect, Cloud Network Engineer, Cloud Security Engineer, Data Engineer, Cloud DevOps Engineer, Cloud Developer, Machine Learning Engineer and Generative AI Leader. 207 named services and concepts from those guides were searched for in the atlas, and the gaps were filled. The atlas covers the *union* of what Google expects of architects, network, security, data, DevOps, developer and ML specialists, at the level of understanding you need, without the exam trivia.
3. **Made specific to your job:** bank controls (VPC-SC, CMEK/EKM, Access Approval, data residency, org policies), UK regulation (operational resilience, SS2/21 outsourcing, SS1/23 model risk, Consumer Duty, UK GDPR) and the current AI stack (Agent Platform, ADK, Agent Runtime, MCP, A2A, Model Armor, RAG, evaluation).
4. **Your unknown unknowns become visible:** rate every concept in the app. Anything you rate "New to me" or "Heard of it" goes on your gap list, so you can see exactly what you don't know.

> **Naming note:** In April 2026 Google renamed Vertex AI to **Gemini Enterprise Agent Platform** (Agent Engine is now **Agent Runtime**, and Vertex AI Search is now **Agent Search**). Colleagues, SDKs and older docs still say "Vertex AI". The atlas uses both names.

## Opening the practice app

- **As a hosted page (recommended):** use the private link Claude published for this repo. Progress saves to your claude.ai account, so it follows you between laptop and phone.
- **Locally:** open `app/index.html` in a browser (download the file, or clone the repo). Progress is saved in that browser.
- After editing the atlas, diagrams or questions, run `python3 tools/build.py` to rebuild the app, the atlas index and `flashcards.csv`.

## The week (no building required, about 2.5–3 hours a day)

Each day covers the **core** concepts of its domains carefully and skims *working* and *aware*. Day 5 brings everything together through architecture.

| Day | Atlas domains (the pieces) | Put it together (Architect section) | Extra practice |
|---|---|---|---|
| **1** | [One-pager](00-gcp-on-one-page.md) · [01 Networking fundamentals](atlas/01-networking-fundamentals.md) · [03 Identity and access](atlas/03-identity-and-access.md) · [10 Governance and cost](atlas/10-governance-and-cost.md) | Read [How to architect](guide/01-how-to-architect.md) §1–5 · Journey: *Who is calling?* · Review: *"Quick win" GenAI pilot* | Diagram: *Static site and API* · scenarios: identity, governance |
| **2** | [02 GCP networking](atlas/02-gcp-networking.md) · [04 Security and compliance](atlas/04-security-and-compliance.md) | Journeys: *On-prem app calls Gemini privately*, *One outbound call, fully controlled* · Lab: *Lift-and-shift* · Review: *Hybrid network* | Diagrams: *Hybrid landing zone*, *Secure data science* · scenarios: networking, security |
| **3** | [05 Compute and containers](atlas/05-compute-and-containers.md) · [06 Storage and databases](atlas/06-storage-and-databases.md) · [07 Data processing](atlas/07-data-processing-and-messaging.md) | Journeys: *Core banking to a regulator's report*, *Scoring a payment in 100 ms* · Labs: *Real-time fraud*, *Governed analytics* · Review: *Self-service analytics* | Diagrams: *Three-tier HA*, *GKE mesh* · scenarios: compute, data |
| **4** | [08 APIs and communication](atlas/08-apis-and-service-communication.md) · [09 Reliability and operations](atlas/09-reliability-and-operations.md) · [11 Migration](atlas/11-migration-and-hybrid.md) | Read §6–7 (knock-on map, failure walk) · Journeys: *Customer adds a payee and pays*, *A zone fails, then a region*, *A code change reaches production* · Labs: *Mobile payments*, *Partner API* · Reviews: *Payments "with HA"*, *DR plan*, *Delivery pipeline*, *KYC intake* | Diagrams: *Active-active payments*, *Open Banking* · scenarios: integration, reliability |
| **5** | [12 AI, ML and agents](atlas/12-ai-ml-and-genai.md) · [13 UK banking regulation](atlas/13-uk-banking-regulation-and-risk.md) | Read §8–10 + the [worked mortgage design](guide/03-worked-designs-and-case-studies.md) · Journey: *An agent's task* · Labs: *Policy assistant (RAG)*, *Servicing agent* · Review: *Servicing agent v0.1* · then one [Google case study](guide/03-worked-designs-and-case-studies.md#part-2-googles-professional-cloud-architect-case-studies), designed by you first | Diagrams: *RAG assistant*, *Agentic servicing*, *Credit-risk MLOps* · scenarios: AI, regulation |

### The daily loop

```
 0:00  Warm-up    (15m)  Re-read the one-pager. Do the flashcards that are due in the app
 0:15  Rate       (30m)  In the atlas, go through today's domains, core tier first. Read each term, say out loud
                         what it is, then rate yourself. Don't open the answers yet
 0:45  Close gaps (60m)  Filter to "My gaps". Open each one, read it properly, follow the Related links,
                         then re-rate. This is where the depth comes from
 1:45  Combine    (40m)  Architect section: today's journey, then design lab, then review. This is the most
                         important block. Reading builds the pieces, and this builds the skill of combining them
 2:25  Recall     (20m)  Blank page: draw one of today's diagrams from memory and label every arrow.
                         Write 5 lines on what surprised you
 2:45  Work       (15m)  Find one of today's concepts in your bank's real environment or design docs
```

Why this works when courses didn't: you **recall before you read** (that's what makes memory stick), you only spend reading time on **your actual gaps**, and the journeys, labs and reviews make you **combine** the knowledge, which is what architecture reviews will ask of you. Fit the extra-practice column (diagram quizzes, scenarios) into the warm-up or the commute.

### After the week

- **Daily, 10 minutes:** due flashcards in the app (or Anki).
- **Weekly:** one design lab or review, one Architecture Center kata (see [practice resources](guide/04-practice-resources.md)), and re-rate one domain.
- **Each design you touch at work:** run it through the [solution design template](cheatsheets/solution-design-template.md) and the 8 lenses before the review.
- **When you have time to build:** the `day-*.md` labs walk you through deploying a Cloud Run app with Firestore, Pub/Sub, BigQuery, Secret Manager and private networking. That's when the knowledge becomes muscle memory.

## Repository layout

```
guide/        how to architect, end-to-end journeys, worked designs + case studies, practice resources
atlas/        13 domain files + generated index (the depth)
practice/     architectures.md, scenarios.md, design-lab.md, design-reviews.md, week1-cards.csv
app/          template.html (source) → index.html (built practice app)
tools/        build.py: rebuilds app/index.html, atlas/README.md, flashcards.csv
cheatsheets/  decision trees, solution design template, gcloud patterns
day-*.md      the original 5-day hands-on track (optional labs)
lab/app/      the Cloud Run app used by the labs
```

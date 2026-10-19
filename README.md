# Learn Google Cloud, in order

A complete, sequenced way to learn Google Cloud for someone who learns on the job, is an **AI engineer in a UK bank**, and has bounced off the 72-hour learning paths. It goes from zero to designing and defending bank-grade cloud and AI systems.

## Start here

**Open the practice app and press "Start lesson 1".** That's the whole instruction.

The app's **Learn** tab runs the [learning path](path/learning-path.md): **43 lessons in 11 stages**, 20–60 minutes each, about 28 hours in total. Each lesson:

1. **Frames the problem:** why these concepts matter, and how they connect to what you learned before.
2. **Teaches the concepts one at a time:** you explain each one to yourself, *then* reveal it and rate yourself. Each concept you study joins your flashcard deck automatically.
3. **Makes you use them immediately:** scenario questions, naming the parts of a real architecture, stepping through an end-to-end journey, making decisions in a design lab, or finding the flaws in someone else's design.
4. **Ends with a checkpoint:** one question that ties it together, answered out loud.

The path runs in dependency order, so each stage builds on the last:

```
 1 Foundations         how GCP is organised: projects, locations, billing, responsibility
 2 Networks            addresses, routes, ports, TCP, DNS, HTTP, TLS, proxies, firewalls
 3 Identity & security tokens, IAM, service accounts, zero trust, keys, perimeters, guardrails
 4 GCP networking      VPCs, private access, Shared VPC, hybrid links, load balancers, edge
 5 Compute             VMs, containers, Kubernetes/GKE, Cloud Run
 6 Data                storage, database theory, GCP databases, BigQuery, pipelines
 7 Services talking    APIs, streaming, messaging, idempotency, retries, sagas
 8 Running it          SLOs, DR, observability, CI/CD, IaC, governance, cost, migration
 9 AI                  ML lifecycle, LLMs, RAG, agents, MCP/A2A, AI safety and governance
10 Banking context     PRA/FCA, operational resilience, outsourcing, UK GDPR, model risk
11 Architect           the design loop, worked designs, Google's case studies, ongoing practice
```

Every core and working concept in the atlas is covered somewhere on the path. The build checks this.

### Every day you study

1. **Flashcards first (10 min).** The Learn page shows how many are due. They come from the concepts you've studied.
2. **Then the next lesson(s).** Press *Continue*. The app remembers where you are, and saves progress to your account, so it works on laptop and phone.
3. **If a checkpoint stumps you,** step back to the concept you're missing (the bar at the top of each lesson). That gap is what to fix.

### Suggested schedule (about 3 hours a day)

| Day | Lessons | What you cover |
|---|---|---|
| 1 | 1–5 | How GCP is organised, and networking fundamentals |
| 2 | 6–9 | Authentication, tokens, IAM, identities for software, zero trust |
| 3 | 10–13 | Keys, secrets, guardrails, perimeters, VPCs, private connectivity |
| 4 | 14–17 | Hybrid connectivity, load balancers and edge, VMs, containers |
| 5 | 18–21 | GKE, Cloud Run, storage, database theory |
| 6 | 22–25 | GCP databases, analytics, data pipelines, APIs |
| 7 | 26–29 | Streaming and API management, messaging, failure patterns, reliability and DR |
| 8 | 30–33 | Observability, delivery, governance and cost, migration |
| 9 | 34–37 | ML, LLMs, RAG, agents |
| 10 | 38–40 | Safe AI, banking regulation |
| 11 | 41–43 | Architecture: the design loop, worked designs and case studies, ongoing routine |

**Only one week?** Do lessons 1–24 (stages 1–6, the platform itself) at about 4 hours a day, then lesson 41 ("The design loop"). Continue the rest at one lesson a day. Going slower is fine. Doing the lessons **in order**, with the recall step, is what matters.

## What's in here (for reference)

The path pulls from these. You can also use them directly to look things up or for extra practice.

| Part | What it is |
|---|---|
| [**Learning path**](path/learning-path.md) | The ordered syllabus above (source for the Learn tab) |
| [**Concept atlas**](atlas/README.md) | 401 concepts in 13 domains, from TCP handshakes to PRA SS1/23. Each has *What*, *How it works*, *On GCP* and *Watch out*, tiered core / working / aware. It's a reference organised **by topic**, not a reading order |
| [**How to architect**](guide/01-how-to-architect.md) | The design loop, the "if you choose X, you must handle Y" knock-on map, failure walks, the questions a bank review board asks, anti-patterns |
| [**End-to-end journeys**](guide/02-end-to-end-journeys.md) | 9 walkthroughs following a request, identity, data, deployment, failure or agent task across a whole architecture |
| [**Worked designs and case studies**](guide/03-worked-designs-and-case-studies.md) | A full worked AI-underwriting design, plus Google's 4 official Professional Cloud Architect case studies analysed |
| [**Practice resources**](guide/04-practice-resources.md) | The best online practice material (Architecture Center, Well-Architected FSI, FINOS, OWASP…), each with an exercise |
| [**Design lab**](practice/design-lab.md) · [**Design reviews**](practice/design-reviews.md) | 7 briefs with 58 graded decisions and twists; 8 flawed proposals to critique |
| [**Architecture library**](practice/architectures.md) · [**Scenarios**](practice/scenarios.md) | 18 bank and AI reference designs (used in hidden-label quizzes); 63 exam-style questions |
| [`flashcards.csv`](flashcards.csv) | All concepts plus 95 original cards, for Anki |
| [One-pager](00-gcp-on-one-page.md) · [cheat sheets](cheatsheets/) | The 8 lenses, service map, decision trees, design template, `gcloud` grammar |
| [Hands-on labs](day-1-foundations.md) (`day-*.md`) | Optional, for when you have time to build: a Cloud Run app that grows through the week |

### App tabs

- **Learn:** the path. Start here, every time.
- **Architect:** readings, journeys, design lab, design reviews (the path sends you here, and you can also browse freely).
- **Atlas:** look up any concept, and rate yourself by domain.
- **Flashcards:** spaced repetition. It defaults to the concepts you've studied.
- **Diagrams:** 18 architectures with labels hidden.
- **Scenarios:** 63 questions by topic.
- **Progress:** lessons done, ratings by domain, your core gaps.

### How do you know nothing important is missing?

The atlas was built bottom-up across 13 domains and cross-checked against Google's official exam guides (Associate Cloud Engineer, Professional Cloud Architect, Network, Security, Data, DevOps, Developer, ML Engineer, Generative AI Leader). 207 named services and concepts from those guides were searched for, and the gaps were filled. It's also tailored to UK banking (VPC-SC, CMEK/EKM, residency, operational resilience, SS2/21, SS1/23, Consumer Duty, UK GDPR) and the current AI stack (Agent Platform, ADK, Agent Runtime, MCP, A2A, Model Armor, RAG, evaluation). Rating yourself shows you what you don't know.

> **Naming note:** In April 2026 Google renamed Vertex AI to **Gemini Enterprise Agent Platform** (Agent Engine is now **Agent Runtime**, and Vertex AI Search is now **Agent Search**). Colleagues, SDKs and older docs still say "Vertex AI". The material uses both names.

## Opening the practice app

- **Hosted (recommended):** the private link Claude published for this repo. Progress saves to your claude.ai account.
- **Locally:** open `app/index.html` in a browser. Progress is saved in that browser.
- After editing any source (path, atlas, guides, practice files), run `python3 tools/build.py`. It rebuilds the app, the atlas index and `flashcards.csv`, and checks that the path covers every core and working concept.

## After the path

- **Daily, 10 minutes:** due flashcards.
- **Weekly:** one design lab or review, plus one Architecture Center kata (see [practice resources](guide/04-practice-resources.md)).
- **Each design at work:** the [60-second checklist](guide/01-how-to-architect.md#10-a-60-second-mental-checklist-memorise-this) and the knock-on map before the review.
- **When you have time to build:** the `day-*.md` labs, or the Cloud Resume Challenge.

## Repository layout

```
path/         learning-path.md: the ordered syllabus (start here)
atlas/        13 domain files + generated index (reference, by topic)
guide/        how to architect, end-to-end journeys, worked designs + case studies, practice resources
practice/     architectures, scenarios, design lab, design reviews, week-1 cards
app/          template.html (source) → index.html (built practice app)
tools/        build.py: builds the app, atlas index and flashcards; validates the path
cheatsheets/  decision trees, solution design template, gcloud patterns
day-*.md      optional hands-on labs; lab/app/ is the Cloud Run app they use
```

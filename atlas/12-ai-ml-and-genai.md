# 12 · AI, ML, generative AI and agents on Google Cloud

The domain closest to your job. Read it with files 03, 04 and 13, because in a bank every AI design gets judged on identity, data protection and model risk as much as on the model.

> **Naming (April 2026):** Vertex AI became **Gemini Enterprise Agent Platform** ("Agent Platform"). Agent Engine is now **Agent Runtime**, Agent Builder's low-code builder is **Agent Studio**, Vertex AI Search is **Agent Search**, and Workbench and Feature Store carry the Agent Platform name. APIs (`aiplatform.googleapis.com`), SDKs and many docs and colleagues still say "Vertex AI". Treat the names as interchangeable.

---

### AI vs ML vs deep learning vs generative AI
`core` · Related: Foundation models, ML lifecycle
**What:** **AI:** systems performing tasks that need human-like intelligence. **ML:** systems that learn patterns from data instead of following hand-written rules. **Deep learning:** ML with multi-layer neural networks. **Generative AI:** models that *produce* new content (text, code, images, audio), mainly **foundation models** (large models pre-trained on broad data and adapted to many tasks). **LLMs** are text and code foundation models built on the transformer architecture.
**Watch out:** Classic ML (credit scoring with gradient-boosted trees, fraud classifiers) is still most production AI in banks. GenAI adds to it rather than replacing it.

### Learning types: supervised, unsupervised, reinforcement
`working` · Related: ML lifecycle, Evaluation metrics
**What:** **Supervised:** learn from labeled examples (fraud / not fraud; predict default probability), as classification or regression. **Unsupervised:** find structure without labels (clustering customer segments, anomaly detection). **Reinforcement learning:** learn by trial and reward. **Self-supervised:** how LLMs pre-train (predict the next token). **RLHF and preference tuning:** align model behaviour with human feedback.

### ML lifecycle
`core` · Related: MLOps, Model monitoring, Model risk management
**What:** Problem framing → data collection and ingestion → **data preparation** and labeling → **feature engineering** → **training** (and hyperparameter tuning) → **evaluation** and validation → **deployment** (online or batch) → **monitoring** (performance, drift) → **retraining** → and around again. Governance runs throughout (documentation, approval, inventory).
**GCP:** Data in BigQuery and Cloud Storage → BigQuery ML or Agent Platform training (AutoML or custom) → Model Registry → endpoints or batch prediction → model monitoring → Pipelines for automation.

### Training vs inference; online vs batch prediction
`core` · Related: GPUs and TPUs, Endpoints
**What:** **Training** builds the model (expensive, periodic). **Inference / serving** uses it to predict or generate (continuous, latency- and cost-sensitive). **Online prediction:** a synchronous, low-latency request per item through an endpoint (real-time fraud scoring). **Batch prediction:** asynchronous scoring of many records at once (nightly propensity scores), cheaper and higher throughput.
**GCP:** Agent Platform **endpoints** (online, autoscaling, with private endpoints through PSC), **batch prediction** jobs (also for Gemini, at reduced cost), BigQuery ML `ML.PREDICT`, Dataflow RunInference, Cloud Run or GKE for self-hosted models.

### Model evaluation metrics
`working` · Related: Supervised learning, LLM evaluation
**What:** Classification: **precision** (of predicted positives, how many are right), **recall** (of actual positives, how many were caught), **F1**, **ROC-AUC / PR-AUC**, a **confusion matrix**. Regression: RMSE, MAE. Always use **train / validation / test splits** (or time-based splits for financial data) to detect **overfitting**.
**Watch out:** Fraud and AML data is heavily imbalanced, so accuracy is meaningless. Precision and recall trade-offs map to costs (false declines vs missed fraud).

### Choosing a model type for tabular and time-series problems
`working` · Related: Learning types, BigQuery ML
**What:** Not every problem needs an LLM. **Tabular classification and regression** (credit risk, propensity, fraud): gradient-boosted trees (XGBoost, boosted trees in BigQuery ML) are usually strong, fast and explainable. **Time-series forecasting** (cash demand, call volumes, liquidity): **ARIMA_PLUS** in BigQuery ML, or foundation forecasting models such as TimesFM. **Deep neural networks (DNNs):** unstructured data, very large datasets. **LLMs:** language understanding and generation, extraction from documents, reasoning with tools.
**Watch out:** Simpler models are easier to validate and explain under model risk management. Use complexity only where it buys accuracy that matters.

### Feature engineering and feature stores
`working` · Related: ML lifecycle, Bigtable, BigQuery
**What:** **Features** are model inputs derived from raw data (for example "number of transactions in the last 1 hour", "days since account opened"). A **feature store** manages feature definitions and serves the *same* values to training (offline, historical, point-in-time correct) and to serving (online, low-latency), which prevents **training/serving skew**.
**GCP:** **Agent Platform Feature Store** (formerly Vertex AI Feature Store) uses BigQuery as the offline store and an online serving layer (optimized or Bigtable-backed) for low-latency lookups.

### Model registry and versioning
`working` · Related: MLOps, Model risk management
**What:** A central catalog of models with versions, lineage (data, code, parameters), evaluation results, aliases (for example `champion` / `challenger`) and deployment status.
**GCP:** **Model Registry** (Agent Platform) works with BigQuery ML models and custom models. It's a natural backbone for the **model inventory** that model risk management rules require.

### MLOps and pipelines
`working` · Related: CI/CD, Model registry, Model monitoring
**What:** DevOps for ML: automated, reproducible pipelines for data validation → training → evaluation → registration → deployment, with **experiment tracking**, **metadata and lineage**, **continuous training** triggers and approval gates.
**GCP:** **Agent Platform Pipelines** (managed Kubeflow Pipelines / TFX), Experiments, ML Metadata, Cloud Build / Cloud Deploy for serving infrastructure. **LLMOps** extends this to prompts, evaluation datasets, RAG indexes and agent versions.

### Model monitoring: skew and drift
`working` · Related: MLOps, Model risk management
**What:** **Training/serving skew:** the features at serving time differ from those at training time (often a pipeline bug). **Data drift:** input distributions shift over time (customer behaviour changes). **Concept drift:** the relationship between inputs and outcome changes (fraud tactics evolve). Monitor input distributions, prediction distributions and, when labels arrive, real performance.
**GCP:** Agent Platform **Model Monitoring** (feature skew and drift detection with alerting), plus your own monitoring in BigQuery. Drift triggers investigation or retraining under the model-risk governance process.

### Explainability
`working` · Related: Model risk management, Consumer Duty, UK GDPR automated decisions
**What:** Understanding *why* a model produced an output. **Global** explanations (which features matter overall) and **local** ones (why *this* customer was declined): feature attributions such as **SHAP** and integrated gradients, counterfactuals ("approved if income were £5k higher"). For LLMs: citations, reasoning traces and grounding sources.
**GCP:** **Explainable AI** (feature attributions on Agent Platform predictions, BigQuery ML `ML.EXPLAIN_PREDICT`).
**Watch out:** In credit and other customer-impacting decisions, explainability is a regulatory expectation (fair treatment, the ability to contest decisions), not a nice-to-have.

### Accelerators and AI Hypercomputer
`working` · Related: GPUs and TPUs, Quotas
**What:** **AI Hypercomputer** is Google's umbrella term for its integrated AI infrastructure: TPUs and GPUs, high-bandwidth networking, storage, software (JAX, PyTorch/XLA, vLLM, GKE and Cluster Director), and **consumption models** (on-demand, Spot, committed use, Dynamic Workload Scheduler for flex-start and calendar reservations).
**GCP:** It matters when you train or self-host models. Hosted Gemini or partner models abstract it away.

### Gemini Enterprise Agent Platform (formerly Vertex AI)
`core` · Related: Model Garden, Agent Runtime, Agent Search, Endpoints
**What:** Google Cloud's unified AI platform for building, deploying and governing ML models, GenAI apps and agents.
**How:** Main parts: **Model Garden** (Gemini, Gemma, Imagen, Veo, Chirp, plus **partner and open models** such as Anthropic Claude, Llama and Mistral, available as managed APIs or self-deployed), **Agent Studio** (low-code agent building), **Agent Development Kit (ADK)** (code-first), **Agent Runtime** (managed agent hosting, formerly Agent Engine), **Agent Search** (managed enterprise search and RAG, formerly Vertex AI Search), RAG Engine, Vector Search, **Gen AI evaluation**, prompt management, tuning, Pipelines, Feature Store, Model Registry, endpoints, Workbench (notebooks), AutoML. Enterprise controls: IAM, **VPC Service Controls**, **CMEK**, **PSC private endpoints**, regional endpoints, data residency commitments, audit logs.
**GCP:** For a bank, the platform's controls (IAM, VPC-SC, CMEK, private connectivity, logging) are what make GenAI approvable.

### Gemini, Gemma and Google's model family
`working` · Related: Model Garden, Choosing a foundation model
**What:** **Gemini:** Google's frontier multimodal models (text, code, images, audio, video in; text and some media out), offered in tiers that trade capability against speed and cost (Pro-class for hard reasoning, Flash-class for fast and cheap, Flash-Lite for high volume), with long context windows, thinking and reasoning modes, function calling, structured output, code execution and grounding. **Gemma:** Google's open-weight models, self-hostable (on GKE, Cloud Run with GPUs, or on-prem). **Imagen / Veo:** image and video generation. **Chirp:** speech.
**Watch out:** Model versions retire on published schedules. Pin versions in production, track deprecation dates, and plan re-validation (a model-risk requirement).

### AI Studio vs Agent Platform
`working` · Related: API keys, VPC Service Controls, Data governance for GenAI
**What:** **Google AI Studio / Gemini Developer API:** quick prototyping with API keys, aimed at developers, with different terms and controls. **Agent Platform Gemini API:** the enterprise route, with IAM, quotas per project, VPC-SC, CMEK, regional processing, audit logs and enterprise data-governance terms.
**Watch out:** Banks should use the enterprise platform for anything touching real data. Most block AI Studio.

### Choosing a foundation model
`working` · Related: Gemini, Model Garden, LLM evaluation
**What:** Weigh: **task quality** (on *your* evaluation set, not public benchmarks), **latency** (time to first token, tokens per second), **cost per token**, **context window**, **modality**, **availability in your region and ML processing location**, **data governance terms**, **quota and capacity**, tool use and structured-output reliability, and **model-risk validation effort**.
**How:** Common pattern: route easy, high-volume tasks to a small, fast model, and hard reasoning to a large model. Re-evaluate when new versions arrive.

### LLM basics: tokens, context window and sampling
`core` · Related: Prompt engineering, Token costs, Hallucination
**What:** **Tokens** are sub-word units (about 4 characters of English each). Models read and write tokens, and pricing and limits are in tokens. The **context window** is the maximum input + output tokens per request (it includes system instructions, history, retrieved documents and tool results). **Sampling parameters:** **temperature** (randomness: low for factual and deterministic tasks, higher for creative ones), **top-p** (nucleus sampling: sample from the smallest set of tokens whose probability adds up to p), **top-k**, **max output tokens**, stop sequences, and safety settings.
**Watch out:** A long context isn't free: cost and latency grow, and models can miss information in the middle of very long contexts. Retrieval beats stuffing everything in.

### Prompt engineering
`core` · Related: LLM basics, Structured output, Few-shot
**What:** Designing inputs to get reliable outputs. **System instructions** (role, rules, tone, constraints), **zero-shot** (just instructions), **one-shot / few-shot** (include examples), **chain-of-thought** or thinking (reason step by step, now often built in as "thinking" modes), **role prompting**, delimiting untrusted content, specifying output format, and **prompt chaining** (break a task into steps).
**How:** Version prompts like code. Evaluate changes against a fixed test set before shipping.

### Structured output and JSON schema
`working` · Related: Function calling, Prompt engineering
**What:** Constraining the model to return output matching a schema (JSON with required fields and enums), through `response_schema` / controlled generation, so downstream code can parse it reliably (for example extracting fields from a loan application).

### Embeddings
`core` · Related: Vector search, RAG, Semantic similarity
**What:** Dense numeric vectors (for example 768 or 3072 dimensions) that represent the *meaning* of text, images or other data. Similar meanings sit close together in vector space (measured by cosine similarity or dot product).
**GCP:** Text and multimodal **embedding models** on Agent Platform (Gemini embeddings), callable from BigQuery (`ML.GENERATE_EMBEDDING`) and AlloyDB (`embedding()` function). Used for semantic search, RAG, clustering, deduplication, recommendations and classification.
**Watch out:** Embeddings from different models aren't compatible. Changing the model means re-embedding the whole corpus.

### Vector search and approximate nearest neighbour (ANN)
`core` · Related: Embeddings, RAG, AlloyDB, BigQuery
**What:** Finding the vectors most similar to a query vector. Exact search compares against every vector (slow at scale). **ANN** indexes (ScaNN, HNSW, IVF) trade a little recall for big speed gains. **Hybrid search** combines vector similarity with keyword search (BM25) and metadata **filters** (for example only documents this user may see, only current policy versions).
**GCP:** **Vector Search** (formerly Vertex AI Vector Search; ScaNN-based, billions of vectors, low latency), **AlloyDB / Cloud SQL pgvector** (with ScaNN in AlloyDB, which keeps vectors next to transactional data and SQL filters), **BigQuery vector search** (`VECTOR_SEARCH`, analytics-scale), Spanner, Firestore and Memorystore vector support, plus managed RAG (Agent Search, RAG Engine).

### Retrieval-augmented generation (RAG)
`core` · Related: Embeddings, Vector search, Grounding, Chunking
**What:** Giving the model relevant, current, private information at query time by **retrieving** it and adding it to the prompt, instead of relying on what the model memorized in training. It reduces hallucination, allows **citations**, and keeps knowledge fresh without retraining.
**How:** **Ingestion:** parse documents (PDF, HTML; layout-aware parsing with Document AI or Gemini) → **chunk** → **embed** → **index**, with metadata (source, date, access-control lists). **Query time:** rewrite or expand the query → retrieve the top-k chunks (hybrid + filters) → optionally **rerank** → build the prompt with the chunks and instructions to cite → generate → return the answer with sources. **Evaluate** retrieval (recall, precision) and generation (groundedness, relevance) separately.
**GCP:** Build it yourself (Cloud Run + AlloyDB or Vector Search + Gemini), or use **RAG Engine** (managed pipeline over your corpora), **Agent Search** (managed enterprise search with connectors and ACLs), or BigQuery-based RAG. Ingestion triggered by Eventarc on new GCS documents is a common pattern.
**Watch out:** Most RAG failures are retrieval failures: bad chunking, missing metadata filters, stale indexes, permissions not enforced at retrieval time.

### Chunking strategies
`working` · Related: RAG, Embeddings
**What:** Splitting documents into retrievable pieces. **Fixed-size** with overlap (simple), **structure-aware** (by headings, sections, tables; best for policies and contracts), **semantic** (split where the topic changes), **hierarchical / parent-child** (retrieve small chunks, pass the larger parent section to the model). Keep metadata (document ID, section, page, effective date, classification) on every chunk.

### Grounding and citations
`working` · Related: RAG, Hallucination
**What:** Tying model outputs to verifiable sources. **Grounding with Google Search** (public web facts), **grounding with your data** (Agent Search, RAG Engine, your own retrieval), grounding with Google Maps or enterprise sources. The response includes **grounding metadata** / citations linking claims to sources, and groundedness can be checked by evaluation.

### Hallucination
`core` · Related: Grounding, LLM evaluation, Human-in-the-loop
**What:** A model generating fluent but false or unsupported content (invented policy clauses, wrong figures, fake citations). It's inherent to how LLMs predict text.
**How:** Mitigations: RAG and grounding with citations, instructions to say "I don't know", constrained or structured outputs, tools for facts and calculations (don't let the model do arithmetic on balances; call a function), verification steps (a second model or rules), evaluation, and **human review** for high-stakes outputs.

### Fine-tuning vs RAG vs prompting
`core` · Related: Prompt engineering, RAG, PEFT
**What:** **Prompting:** fastest and cheapest. Try it first. **RAG:** adds *knowledge* (facts, documents, changing data). **Fine-tuning / tuning:** changes *behaviour* (style, format, domain-specific tasks, classification) using labeled examples. **Supervised fine-tuning**, **preference tuning**, **distillation** (train a small model to imitate a large one for cost and latency).
**How:** **PEFT / LoRA** (parameter-efficient fine-tuning) trains small adapter weights instead of the whole model, so it's cheaper. Agent Platform offers managed tuning for Gemini and open models.
**Watch out:** Fine-tuning doesn't reliably teach facts and needs re-validation with each base-model change. For knowledge, use RAG. A tuned model is also a new model for model-risk purposes.

### Function calling and tool use
`core` · Related: Agents, MCP, OpenAPI
**What:** The model is given **tool declarations** (name, description, JSON schema of parameters). Instead of answering directly, it can return a structured **function call**. *Your code* executes it (calls an API, queries a database) and returns the result, and the model continues.
**How:** The model never executes anything itself. The application decides whether and how to run each call, which is your control point for authorization, validation and logging. Tool descriptions are effectively prompts, so write them carefully.
**Watch out:** Every tool is an attack surface. Least-privilege tool identities, input validation, and human confirmation for consequential actions (payments, emails to customers).

### AI agents
`core` · Related: Function calling, ADK, Agent Runtime, Multi-agent systems
**What:** Systems where an LLM **decides the next step** in a loop: **reason / plan → act (call a tool) → observe the result → repeat** until the goal is met. Agents combine a model, instructions, **tools**, **memory / state**, and orchestration logic.
**How:** There's a spectrum from **deterministic workflows** (fixed steps, with an LLM at certain points; predictable and auditable) to **autonomous agents** (the LLM chooses steps; flexible, less predictable). **Multi-agent** systems split work among specialist agents (a router, a researcher, a writer), coordinated by an orchestrator or by agent-to-agent protocols.
**Watch out:** In regulated settings, prefer the most deterministic design that solves the problem, keep a human in the loop for consequential actions, log every step, and evaluate **trajectories** (the steps taken), not only final answers.

### Agent Development Kit (ADK)
`core` · Related: AI agents, Agent Runtime, A2A protocol, MCP
**What:** Google's open-source, code-first framework for building agents and multi-agent systems (Python, Java, Go, TypeScript). It's model-agnostic, but optimized for Gemini and Agent Platform.
**How:** **Agents:** `LlmAgent` (an LLM with instructions and tools), **workflow agents** (`SequentialAgent`, `ParallelAgent`, `LoopAgent`) for deterministic orchestration, and custom agents. **Tools:** Python functions, built-in tools (Google Search, code execution), **OpenAPI tools**, **MCP tools**, other agents used as tools, and Google Cloud integrations. **Sessions, state and memory** services, **callbacks** (before and after model or tool calls: guardrails, logging, PII redaction), **artifacts**, **evaluation** (`adk eval` against test sets, including trajectories), a dev UI, streaming (bidirectional audio and video), and **A2A** support. Deploy to **Agent Runtime**, **Cloud Run** or **GKE**. The `agents-cli` scaffolding generates FastAPI serving, A2A endpoints and deployment configuration.

### Agent Runtime (formerly Agent Engine)
`working` · Related: ADK, Sessions and memory, Cloud Run
**What:** Managed infrastructure on Agent Platform for deploying, scaling and governing agents built with ADK, LangGraph, LangChain, CrewAI, LlamaIndex or custom code.
**How:** Provides managed **sessions** (conversation state), **Memory Bank** (long-term memory across sessions), a sandboxed **code execution** environment, built-in tracing, logging and monitoring, evaluation integration, IAM, VPC-SC and private networking options, plus agent identity.
**GCP:** Compared with Cloud Run, Agent Runtime gives you agent-specific managed services with less plumbing. Cloud Run gives full control over the container, networking and serving stack (and is where many existing FastAPI-based agent servers live).

### Sessions, state and memory
`working` · Related: Stateless vs stateful services, Agent Runtime
**What:** **Session:** one conversation thread (events and messages). **State:** key/value data scoped to the session, user or app (for example the selected account, a draft in progress). **Memory:** long-term knowledge recalled across sessions (user preferences, prior cases), usually extracted and retrieved semantically.
**Watch out:** Memory holds personal data. Apply retention limits, access controls, the right to erasure, and don't let memory become an unmanaged copy of customer data.

### Model Context Protocol (MCP)
`core` · Related: Function calling, ADK, Apigee
**What:** An open protocol (originally from Anthropic) that standardizes how AI applications connect to tools and data. **MCP servers** expose **tools** (actions), **resources** (data) and **prompts**. **MCP clients** inside host applications (IDEs, chat apps, agents) discover and call them.
**How:** Transports: **stdio** (local processes) and **streamable HTTP** (remote servers, using SSE for streaming). Authorization for remote servers is based on **OAuth 2.1**. One MCP server can serve many agent frameworks and models, so integrations are built once.
**GCP:** Host MCP servers on **Cloud Run** (with IAM or IAP authentication), consume them from ADK (`McpToolset`), and put **Apigee** in front for governance. Google also provides MCP servers for some of its own services (for example databases through the MCP Toolbox for Databases). Check current availability.
**Watch out:** Third-party MCP servers are code and tool descriptions you're trusting. Tool-description poisoning and over-broad tokens are real risks. Allow-list approved servers.

### Agent2Agent protocol (A2A)
`core` · Related: ADK, MCP, Multi-agent systems
**What:** An open protocol (started by Google, now under the Linux Foundation) for **agents to communicate with other agents** across frameworks, vendors and organizations. MCP connects an agent to *tools*. A2A connects an agent to *other agents* that have their own reasoning.
**How:** Each agent publishes an **Agent Card** (JSON metadata at a well-known URL: name, skills, endpoint, supported auth schemes and capabilities). Clients send **messages** (made of **parts**: text, files, data) over **JSON-RPC 2.0 on HTTPS**, creating **tasks** with a lifecycle (submitted, working, input-required, completed, failed) that produce **artifacts**. It supports **streaming (SSE)** and **push notifications** for long-running tasks. Security uses standard HTTP auth (OAuth/OIDC, API keys, mTLS), declared in the card.
**GCP:** ADK agents can be exposed as A2A servers (the `agents-cli` scaffold generates the A2A adapter) and can call remote A2A agents. Agent Runtime and Cloud Run host them. In an enterprise, this enables a catalogue of team-owned agents that other agents can delegate to.

### LLM and agent evaluation
`core` · Related: Hallucination, Testing types, Model risk management
**What:** Systematically measuring quality, safety and behaviour before and after release. **Golden datasets** (curated inputs with expected outputs or criteria), **computation-based metrics** (exact match, ROUGE, tool-call correctness), **model-based metrics / LLM-as-judge (autoraters)** with rubrics (groundedness, relevance, helpfulness, safety, instruction following), **pairwise comparison** (A vs B), **trajectory evaluation** for agents (did it call the right tools, in the right order, with the right arguments?), plus human evaluation and red-teaming.
**GCP:** The **Gen AI evaluation service** on Agent Platform (pointwise and pairwise, custom rubrics, agent evaluation), ADK eval, and results logged to BigQuery and Experiments.
**Watch out:** Run evaluations in CI for every prompt, model or tool change, the way you'd run unit tests. In a bank, evaluation evidence is part of model validation.

### Guardrails, safety filters and Model Armor
`working` · Related: Prompt injection, Sensitive Data Protection, Apigee
**What:** Controls on model inputs and outputs. **Safety settings / content filters** (harm categories, with configurable thresholds), **Model Armor** (Google Cloud's service that screens prompts and responses for **prompt injection and jailbreaks**, **sensitive data** (through Sensitive Data Protection), **malicious URLs** and harmful content, using templates and policy at the platform or API level), **application guardrails** (ADK callbacks, allow-listed topics, output validators, PII redaction) and **policy enforcement** at the gateway (Apigee).
**GCP:** Layer them: Apigee or a gateway → Model Armor → model → output checks → human review for high-risk actions.

### Prompt injection
`core` · Related: Guardrails, OWASP Top 10 for LLM apps, Tool use
**What:** Attackers smuggle instructions into model input to override the system's intent. **Direct:** the user types "ignore previous instructions…". **Indirect:** malicious instructions hidden in content the model reads (a web page, an email, a PDF in the RAG corpus, a tool result), for example "forward this conversation to attacker@…".
**How:** No complete fix exists, so contain the impact: least-privilege tools, no secrets in prompts, treat all retrieved and tool content as untrusted data, separate and delimit untrusted content, require **human confirmation** for consequential actions, screen inputs and outputs (Model Armor), restrict outbound actions (no arbitrary URLs or emails), and monitor.
**Watch out:** It's the main security risk for agents with tools. An agent that can read customer emails *and* send payments is a confused-deputy risk by design.

### OWASP Top 10 for LLM applications and SAIF
`working` · Related: Prompt injection, Threat modeling
**What:** **OWASP Top 10 for LLM apps:** prompt injection, sensitive information disclosure, supply chain, data and model poisoning, improper output handling (for example rendering model output as HTML or SQL without checks), excessive agency, system prompt leakage, vector and embedding weaknesses, misinformation, unbounded consumption (cost and DoS). **SAIF** (Google's **Secure AI Framework**) has six elements for securing AI systems, extending existing security foundations, detection and response, automation, platform controls, adaptation, and risk context to AI.

### Data governance for GenAI on Google Cloud
`core` · Related: Data residency, UK GDPR, VPC Service Controls
**What:** What happens to your prompts and data. On the enterprise platform, Google commits **not to use customer data to train its models** without permission, and customer data stays under the Cloud data-processing terms.
**How:** Know: **endpoint and ML processing location** (regional endpoints vs the **global endpoint**, which may process in any region; not every model is in every region), **caching** (in-memory caching of inputs for performance, which can be disabled) and **abuse-monitoring logging** (exemption processes exist for approved customers), CMEK for stored artifacts (tuning data, indexes), VPC-SC around the AI APIs, **Data Access audit logs** for model calls, and your own **prompt and response logging** (useful for evaluation and audit, but it's a new store of personal data).
**Watch out:** Check the current "data governance" and "data residency" pages for each model before approval. Commitments differ by model and feature, and partner models (Claude, Llama) have their own terms through Model Garden.

### Quotas, Provisioned Throughput and 429 handling
`working` · Related: Quotas and limits, Retries
**What:** Gemini on Agent Platform uses **dynamic shared quota** for many models (capacity shared across customers, so bursts can get **429 Resource Exhausted**) and offers **Provisioned Throughput** (reserved capacity in throughput units, bought for a term) for guaranteed, predictable performance.
**How:** Handle 429s with retries with backoff and jitter, client-side rate limiting, queueing (Cloud Tasks or Pub/Sub) for non-interactive work, fallback models or regions, and Provisioned Throughput for critical customer-facing paths.

### Token costs, context caching and batch
`working` · Related: FinOps, LLM basics
**What:** Cost = input tokens × input price + output tokens × output price (+ thinking tokens, grounding fees, tool calls). Output tokens usually cost several times more. Levers: smaller models for easy tasks, shorter prompts, retrieval instead of stuffing, **context caching** (reuse a large repeated prefix such as a policy manual at a discount; implicit and explicit caching), **batch prediction** (discounted asynchronous jobs), and response caching for repeated questions.
**Watch out:** Agents multiply tokens: every loop re-sends the history and tool results. Track **cost per completed task**, not per call.

### Latency for LLM apps
`working` · Related: Server-sent events, Model choice
**What:** **Time to first token (TTFT)** (perceived responsiveness) vs **tokens per second** (completion speed) vs end-to-end task time (agents with many steps). Improve with streaming (SSE), smaller and faster models, parallel tool calls, caching, shorter outputs, regional proximity, and fewer sequential agent steps.

### Human-in-the-loop
`working` · Related: AI agents, Workflows, Consumer Duty
**What:** A human reviews, approves or corrects AI outputs or actions at defined points: approving a payment the agent prepared, an underwriter validating an AI-drafted credit memo, an analyst confirming a suspicious-activity narrative.
**GCP:** Workflows callbacks, ADK tool confirmations, case-management integrations. It's usually required where outcomes affect customers or regulatory filings.

### Responsible AI: fairness, bias and transparency
`working` · Related: Explainability, Consumer Duty, Model risk management
**What:** Ensuring AI systems are fair (no unjustified differences in outcomes across protected characteristics), transparent (people know when AI is used and why decisions were made), accountable (clear ownership), privacy-preserving, safe and robust.
**How:** Measure bias across groups (with care around proxies such as postcode), use representative data, document models (model cards, data sheets), check that disclosures to customers are accurate, give customers a way to contest decisions, and monitor after deployment.

### Document AI
`working` · Related: RAG, KYC
**What:** Managed document processing: OCR, layout parsing, form and table extraction, and specialized processors (identity documents, bank statements, invoices, pay slips), plus custom extractors and classifiers built on generative models.
**GCP:** Bank uses: KYC and onboarding document extraction, mortgage document processing, layout-aware parsing for RAG ingestion.

### Pre-built AI APIs
`aware` · Related: Document AI
**What:** Task-specific APIs: **Speech-to-Text** and **Text-to-Speech** (contact-centre transcription, voice agents), **Translation**, **Natural Language** (entities, sentiment), **Vision** (labels, OCR), **Video Intelligence**. Often the cheapest, most predictable option for narrow tasks.

### Gemini Enterprise, NotebookLM and Customer Engagement Suite
`aware` · Related: Agent Search, AI agents
**What:** **Gemini Enterprise** (formerly Agentspace): an employee-facing platform for enterprise search across connected systems, prebuilt agents and agent creation, with access controls. **NotebookLM Enterprise:** research and summarization over your own sources. **Customer Engagement Suite:** contact-centre AI: conversational agents (voice and chat bots), Agent Assist (real-time help for human agents), Conversational Insights (analytics). These are "buy" options to weigh against building with ADK.

### Gemini Code Assist and AI-assisted engineering
`aware` · Related: CI/CD, Testing types
**What:** AI coding assistance in IDEs and on the command line (Gemini Code Assist, Gemini CLI, and others), including test generation, code review and code transformation. Enterprise editions add code customization on private repositories and data-protection terms. The new exam guides include AI-assisted development.

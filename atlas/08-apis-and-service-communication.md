# 08 · APIs, service communication and distributed-system patterns

How services talk to each other, how APIs are exposed and governed, and the patterns that stop distributed systems failing in strange ways.

---

### Synchronous vs asynchronous communication
`core` · Related: Request/response vs event-driven, Pub/Sub, Timeouts
**What:** **Synchronous:** the caller sends a request and waits for the response (REST, gRPC). It's simple and immediate, but it couples availability (if B is down, A fails) and latency (A's latency includes B's). **Asynchronous:** the caller hands off a message or event and continues (Pub/Sub, Kafka, Cloud Tasks). It decouples availability and buffers load, at the cost of eventual consistency, harder debugging and more complex error handling.
**How:** Rule of thumb: synchronous for queries and anything the user is waiting on. Asynchronous for side effects, fan-out, long-running work and integration between domains.
**Watch out:** A chain of synchronous calls multiplies failure probability. Five services at 99.9% each give about 99.5% end to end.

### Request/response vs event-driven architecture
`core` · Related: Synchronous vs asynchronous, Eventarc, Choreography vs orchestration
**What:** **Request/response:** "do this for me and tell me the result" (a command). **Event-driven:** services publish **events** ("PaymentSettled") describing facts that happened, and interested services react independently. Producers don't know who the consumers are.
**How:** Event types: **notification** (thin: an ID, so consumers call back for details), **event-carried state transfer** (fat: includes the data), **domain events**.
**GCP:** Pub/Sub, Eventarc (with the CloudEvents format), Kafka. For example, a "transaction posted" event fans out to fraud scoring, notifications, the ledger analytics feed and an agent that categorizes the spend.

### REST
`core` · Related: HTTP basics, HTTP status codes, OpenAPI
**What:** An architectural style for HTTP APIs: **resources** identified by URLs (`/accounts/123/transactions`), manipulated with standard **methods**, **stateless** requests, representations (usually JSON), and meaningful **status codes**.
**How:** GET reads, POST creates (or triggers an action), PUT replaces, PATCH partially updates, DELETE removes. Collections support filtering, sorting and pagination. Versioning goes in the path (`/v1/`) or headers.
**GCP:** Almost every Google API is available as REST (and gRPC). Google's **API Improvement Proposals (AIPs)** are a good REST design guide (resource names, standard methods, long-running operations, pagination).

### HTTP methods: safety and idempotency
`core` · Related: Idempotency, Retries
**What:** **Safe** methods don't change state: GET, HEAD, OPTIONS. **Idempotent** methods have the same effect whether called once or many times: GET, PUT, DELETE (plus HEAD, OPTIONS). **POST is not idempotent** and PATCH isn't guaranteed to be.
**Watch out:** Clients and proxies retry idempotent requests freely. A retried POST "make payment" can pay twice unless the API supports **idempotency keys**.

### HTTP status codes
`core` · Related: REST, Retries
**What:** **2xx** success: 200 OK, 201 Created, 202 Accepted (async processing started), 204 No Content. **3xx** redirect: 301/308 permanent, 302/307 temporary, 304 Not Modified. **4xx** client error: 400 Bad Request, **401 Unauthorized** (actually *unauthenticated*), **403 Forbidden** (authenticated but not allowed), 404 Not Found, 409 Conflict, 412 Precondition Failed (etag mismatch), **429 Too Many Requests** (rate limited; respect `Retry-After`). **5xx** server error: 500 Internal, **502 Bad Gateway** (a proxy got a bad response from upstream), **503 Service Unavailable** (overloaded or down; retryable), **504 Gateway Timeout** (upstream too slow).
**Watch out:** Only retry 429, 503, 504 and idempotent requests after timeouts or connection errors. Never blindly retry 4xx.

### gRPC and Protocol Buffers
`core` · Related: HTTP/2, REST, Service mesh
**What:** **gRPC** is a high-performance RPC framework. Services and messages are defined in **Protocol Buffers** (`.proto`), a compact binary serialization format with strong schemas, and client and server code is generated from them. It runs over **HTTP/2**.
**How:** Four call types: **unary** (request → response), **server streaming** (request → stream of responses), **client streaming**, **bidirectional streaming**. Built-in **deadlines** (propagated across hops), cancellation, metadata (headers), status codes, and backward-compatible schema evolution (field numbers; never reuse them).
**GCP:** Many Google APIs are gRPC-native (Pub/Sub, Spanner, Bigtable clients). **Cloud Run** supports gRPC, including streaming, with HTTP/2 end-to-end. Application Load Balancers and service mesh route gRPC. **gRPC-Web** or **transcoding** (API Gateway, Cloud Endpoints, Envoy) exposes gRPC services as REST/JSON to browsers.
**Watch out:** It's great for internal service-to-service calls (fast, typed, streaming). It's less friendly for public, browser-facing or partner APIs, where REST/JSON plus OpenAPI is the norm.

### GraphQL
`working` · Related: REST, API gateway
**What:** A query language for APIs. Clients ask for exactly the fields they need from a typed schema in one request, which avoids over- and under-fetching across many REST calls. It has one endpoint, and mutations for writes and subscriptions for push.
**Watch out:** Caching, authorization per field and query cost control (deeply nested queries) are harder than with REST. Apigee supports GraphQL proxies with schema validation.

### WebSockets
`working` · Related: Server-sent events, HTTP basics, Cloud Run
**What:** A full-duplex, long-lived connection over a single TCP connection, started with an HTTP `Upgrade` handshake. Either side can send messages at any time.
**GCP:** Supported on Cloud Run (bounded by the request timeout, up to 60 minutes; clients must reconnect), GKE and Application Load Balancers (backend service timeout). Scaling needs care: connections pin to instances, so use session affinity and shared state through Memorystore pub/sub or similar.
**GCP use:** Live trading UIs, chat, real-time voice agents (for example the Gemini Live API).

### Server-sent events (SSE) and streaming responses
`core` · Related: WebSockets, LLM basics, A2A protocol
**What:** A one-way stream from server to client over a normal HTTP response (`Content-Type: text/event-stream`). The server keeps the response open and writes `data:` lines as events occur. It's simpler than WebSockets and works through most HTTP infrastructure.
**How:** It's the standard way LLM APIs **stream tokens** to clients, and it's used by MCP (streamable HTTP) and A2A for streaming updates.
**Watch out:** Proxies, gateways and load balancers that *buffer* responses break streaming. Check timeouts and buffering settings on every hop (Apigee, load balancer, Cloud Run).

### Long polling and webhooks
`working` · Related: Server-sent events, Idempotency, HMAC
**What:** **Long polling:** the client sends a request, and the server holds it until data is available or a timeout, then the client immediately re-asks. **Webhooks:** the provider calls *your* HTTP endpoint when something happens (a callback), for example a payment-provider status update.
**How:** Webhook receivers must **verify authenticity** (an HMAC signature header, mTLS, or an OIDC token), respond fast (queue the work and return 2xx), be **idempotent** (providers retry), and tolerate out-of-order delivery.
**GCP:** Pub/Sub push subscriptions and Eventarc are webhooks with OIDC authentication. Cloud Run is the usual receiver, often writing straight to Pub/Sub or Cloud Tasks.

### API design: versioning, pagination, errors, long-running operations
`working` · Related: REST, OpenAPI, API management
**What:** **Versioning:** major versions in the path, additive changes within a version, deprecation policies. **Pagination:** prefer cursor or page tokens over offsets (stable under inserts). **Errors:** a consistent error model (code, message, details), as in Google's `google.rpc.Status`. **Long-running operations:** return 202 + an operation resource the client polls (or a callback), which is how Google APIs handle slow tasks. **Field masks** for partial updates and reads. **Etags** for optimistic concurrency.

### OpenAPI
`working` · Related: REST, Apigee, API Gateway
**What:** A standard, machine-readable specification (YAML or JSON) for REST APIs: paths, operations, parameters, schemas and security schemes. It drives documentation, client and server generation, mocking, testing and gateway configuration.
**GCP:** API Gateway and Cloud Endpoints are configured from OpenAPI specs. Apigee imports OpenAPI to generate proxies and developer-portal docs. **Agents use OpenAPI specs as tool definitions**, so well-described APIs become agent tools quickly.

### Idempotency and idempotency keys
`core` · Related: Delivery semantics, Retries, Webhooks
**What:** An operation is **idempotent** if repeating it has the same effect as doing it once. **Idempotency keys** make non-idempotent operations safe: the client sends a unique key (for example a UUID per payment attempt), and the server stores key → result and returns the stored result for repeats instead of executing again.
**How:** Store keys with a TTL, atomically with the side effect (same transaction), and scope them per client. Consumers of at-least-once messages dedupe on message or business IDs.
**Watch out:** In financial systems this is non-negotiable: network timeouts and retries **will** happen, and "did my payment go through?" must have one answer.

### Retries, exponential backoff and jitter
`core` · Related: Idempotency, Circuit breaker, HTTP status codes
**What:** Retrying transient failures (timeouts, 429, 503) with **exponentially growing waits** (for example 100 ms, 200 ms, 400 ms… capped) plus **random jitter**, so that many clients don't retry in sync and hammer a recovering service.
**How:** Limit attempts, and set an overall deadline. Retry only idempotent operations or those with idempotency keys. Use **retry budgets** (for example retries must stay under 10% of requests) to avoid retry storms.
**GCP:** Google client libraries retry automatically with backoff for retryable errors. Pub/Sub has retry policies. Cloud Tasks and Workflows have configurable retries.
**Watch out:** Retries at every layer multiply: 3 retries × 3 layers = 27 attempts on the bottom service. Retry at one layer.

### Timeouts, deadlines and deadline propagation
`core` · Related: gRPC, Retries, Circuit breaker
**What:** Every remote call needs a **timeout**. Without one, a slow dependency holds threads and connections until the caller collapses too. A **deadline** is an absolute "must finish by" time, **propagated** down the call chain so downstream services stop work the caller has already given up on.
**How:** Set timeouts per hop that add up to less than the user-facing budget. gRPC propagates deadlines natively.
**GCP:** Cloud Run request timeout, load balancer backend timeout, Apigee target timeouts, client library timeouts. LLM calls have long and variable latency, so budget for them explicitly and stream.

### Circuit breaker
`working` · Related: Retries, Graceful degradation, Service mesh
**What:** Wraps calls to a dependency. After repeated failures it **opens** (fails fast, without calling the dependency, maybe returning a fallback). After a cool-down it goes **half-open** to test with a few calls, then **closes** if healthy.
**How:** It prevents wasting resources on a dead dependency and gives the dependency room to recover.
**GCP:** In code (resilience libraries) or in a service mesh / Envoy (outlier detection, connection limits). Load balancer outlier detection is a related mechanism.

### Bulkheads, rate limiting and throttling
`core` · Related: Apigee, Cloud Armor, Backpressure
**What:** **Bulkheads:** isolate resources (thread pools, connection pools, instances) per dependency or tenant, so one failure can't sink the whole service. **Rate limiting:** cap requests per client or key in a time window. Algorithms are **token bucket** (allows bursts up to the bucket size), **leaky bucket** (smooth rate) and fixed or sliding windows. **Throttling** is the response: reject with 429 or delay.
**GCP:** Apigee (Quota, SpikeArrest policies), Cloud Armor rate-limiting rules, API Gateway quotas, Cloud Tasks queue rates, and Gemini model quotas (protect yourself from the provider's 429s too).

### Backpressure and load shedding
`working` · Related: Pub/Sub, Rate limiting, Graceful degradation
**What:** **Backpressure:** a slow consumer signals producers to slow down, instead of buffering until it runs out of memory (flow control in Pub/Sub StreamingPull, TCP windows, reactive streams). **Load shedding:** under overload, deliberately reject low-priority work early, so high-priority requests still succeed.
**GCP:** A queue (Pub/Sub, Cloud Tasks) between bursty producers and fragile consumers is the classic buffer. Its backlog becomes the autoscaling signal.

### API gateway vs API management
`core` · Related: Apigee, API Gateway, Reverse proxy
**What:** An **API gateway** is a reverse proxy in front of APIs that does routing, authentication, rate limiting and transformation. **API management** adds the full lifecycle around it: a **developer portal** (documentation and self-service keys), **API products** and plans, analytics, monetization, versioning, security policies, and governance across many teams and external consumers.
**GCP:** **API Gateway** is lightweight and serverless, for simple backends. **Apigee** is enterprise API management. Cloud Endpoints is legacy.

### Apigee
`core` · Related: API gateway vs API management, OAuth 2.0, Private Service Connect
**What:** Google's enterprise API management platform. Very common in banks for external, partner and **Open Banking** APIs, and increasingly for governing access to internal APIs and AI models.
**How:** You define **API proxies**: a **proxy endpoint** (client-facing, "northbound") and **target endpoint** (backend, "southbound"), with **flows** of **policies** attached: **VerifyAPIKey**, **OAuthV2** (Apigee as the authorization server, issuing and validating tokens), **VerifyJWT**, **Quota**, **SpikeArrest**, **JSONThreatProtection / RegexProtection**, **AssignMessage** (transform), **ResponseCache**, **ServiceCallout**, JavaScript or Java callouts, and shared flows (reusable policy chains, for example a corporate security flow). **API products** bundle proxies, scopes and quotas. **Apps and developers** get credentials. There's an integrated **developer portal**, **analytics**, **monetization** and **Advanced API Security** (abuse detection, security scoring). Deployment models: **Apigee X** (Google-managed; networking northbound through an external or internal load balancer, or PSC, and southbound to backends through PSC or VPC peering) and **Apigee hybrid** (you run the runtime plane on your own Kubernetes on-prem or in another cloud, while Google hosts the management plane).
**GCP:** **Apigee as an AI gateway**: proxies in front of model endpoints (Gemini, Claude through Model Garden, internal models) enforce authentication, **token-based quotas** per team, PII checks (calling Sensitive Data Protection or Model Armor), logging, semantic caching and model routing, giving one governed front door for every LLM call in the bank. Check current Apigee docs for the latest LLM-specific policies.

### API Gateway and Cloud Endpoints
`working` · Related: Apigee, OpenAPI
**What:** **API Gateway:** a fully managed gateway configured from an OpenAPI spec, for Cloud Run, Cloud Run functions and App Engine backends, with API keys, JWT validation and quotas. Cheaper and simpler than Apigee, but without a portal, monetization or rich policies. **Cloud Endpoints:** the older option based on the Extensible Service Proxy (ESPv2/Envoy) sidecar.

### Service discovery
`working` · Related: Kubernetes Services, Cloud DNS, Service mesh
**What:** How a service finds the current network location of another. **DNS-based** (Kubernetes Service DNS names, Cloud DNS private zones), **registry-based** (Service Directory, Consul), or handled by the **mesh**.
**GCP:** Cloud Run services have stable URLs (discovery is easy). In GKE, use `service.namespace.svc.cluster.local`. Service Directory registers endpoints across GKE, VMs and on-prem.

### Monolith vs microservices
`core` · Related: Service mesh, Event-driven architecture, Strangler fig
**What:** A **monolith** deploys as one unit: simple to build, test and run; it scales as a whole, and coordinating releases gets harder as teams grow. **Microservices** are independently deployable services around business capabilities, each owning its data: they allow independent scaling and release, at the cost of distributed-systems complexity (network failures, eventual consistency, observability, many deployments).
**How:** A **modular monolith** is often the right first step. Split out services where independent scaling, team autonomy or different release cadences pay for the complexity.
**Watch out:** A "distributed monolith" (services that must deploy together and share a database) gets the worst of both.

### Choreography vs orchestration
`core` · Related: Saga pattern, Workflows, Event-driven architecture
**What:** **Orchestration:** a central coordinator tells each service what to do and tracks the overall state (for example Workflows, Composer, an agent orchestrator). It's easy to see and change the flow, but the coordinator becomes coupled to everything. **Choreography:** services react to each other's events with no central controller. It's loosely coupled, but the end-to-end flow is implicit and harder to trace.
**GCP:** Orchestration: **Workflows**, Cloud Composer, Cloud Tasks chains, ADK workflow agents. Choreography: Pub/Sub and Eventarc.

### Saga pattern (distributed transactions)
`working` · Related: Choreography vs orchestration, ACID, Idempotency
**What:** Keeping data consistent across services *without* a distributed ACID transaction. A saga is a sequence of local transactions, each with a **compensating action** that undoes it if a later step fails (reserve funds → book FX → transfer; if the transfer fails, release the FX booking, then release the funds).
**How:** It can be orchestrated (a coordinator such as Workflows) or choreographed (events). Every step and compensation must be idempotent.
**Watch out:** Between steps the system is temporarily inconsistent, and compensations aren't always possible (you can't un-send an email). Design for that.

### Transactional outbox
`working` · Related: Change data capture, Delivery semantics, Saga
**What:** Solves the "dual write" problem: updating your database *and* publishing an event can't be atomic across two systems. Instead, write the event to an **outbox table in the same database transaction** as the business change. A separate relay (a poller, or CDC) publishes outbox rows to Pub/Sub or Kafka.
**GCP:** Cloud SQL or AlloyDB outbox + a Datastream or Debezium relay, or Spanner change streams → Dataflow → Pub/Sub.

### CQRS and event sourcing
`aware` · Related: Event-driven architecture, Data lake
**What:** **CQRS** (Command Query Responsibility Segregation) uses separate models for writes and reads (for example writes to Spanner, reads from a denormalized BigQuery or Elasticsearch view). **Event sourcing** stores state as an append-only log of events and derives current state by replaying them. That gives a full audit history, which suits ledgers, but adds complexity.

### Eventarc
`core` · Related: Pub/Sub, Event-driven architecture, Cloud Run
**What:** GCP's event routing service. It delivers events in the **CloudEvents** format from sources to targets.
**How:** Sources: **direct events** (Cloud Storage object finalized, Pub/Sub messages, Firestore changes, and more), **Cloud Audit Logs events** (almost any API call on GCP, for example "a BigQuery table was created"), and third-party providers. Targets: Cloud Run, Cloud Run functions, GKE services, Workflows, internal HTTP endpoints. Triggers have filters, and run as a service account that needs invoker rights. **Eventarc Advanced** adds a central message bus with routing, filtering and transformation across many publishers and subscribers.
**GCP:** "When a document lands in this bucket, start the RAG ingestion job" is a one-trigger Eventarc pattern.

### CloudEvents
`aware` · Related: Eventarc
**What:** A CNCF specification for describing events in a common way (`id`, `source`, `type`, `time`, `subject`, `data`), so producers and consumers across platforms interoperate.

### Cloud Tasks
`working` · Related: Pub/Sub, Rate limiting, Retries
**What:** Managed **queues of HTTP (or App Engine) tasks**, where each task is a request to a *specific* target. You get explicit control: **rate limits** (dispatches per second, max concurrent), **retries** with backoff, **scheduled delivery** (run at time X), and **deduplication** by task name.
**GCP:** Use it to protect a fragile downstream (a legacy core banking API that can take only 50 requests per second), or for deferred work per user. Pub/Sub is better for fan-out and decoupled events, where the publisher doesn't know the consumers.

### Cloud Scheduler
`working` · Related: Cloud Run jobs, Workflows
**What:** A managed **cron** service. It triggers HTTP targets (with OIDC or OAuth authentication), Pub/Sub topics or App Engine on a schedule, with retries.

### Workflows
`working` · Related: Choreography vs orchestration, Saga pattern, Eventarc
**What:** Serverless **orchestration** of services and APIs, defined in YAML or JSON: steps, conditions, loops, parallel branches, variables, **try/retry/except** error handling, **connectors** for Google APIs (with long-running operations handled for you), **callbacks** (wait for external events or human approval), and executions that can last up to a year.
**GCP:** Good for sagas, document-processing pipelines, approval flows ("generate a credit memo with Gemini → wait for underwriter approval via callback → file it"), and gluing Cloud Run services together without writing orchestration code.

### Application Integration and Integration Connectors
`aware` · Related: Workflows, Apigee
**What:** Google's iPaaS: low-code integration flows with **Integration Connectors** to SaaS and enterprise systems (Salesforce, SAP, ServiceNow, databases, mainframes and so on). The connectors can also be exposed as tools for AI agents.

### Serialization formats
`working` · Related: gRPC and Protocol Buffers, Data lake
**What:** How data is encoded on the wire or on disk. **JSON** (human-readable, flexible, verbose), **Protocol Buffers** (binary, schema'd, compact, the RPC standard), **Avro** (binary, schema travels with the data, common in Kafka and Pub/Sub schemas), **Parquet / ORC** (columnar files for analytics, used in data lakes and BigLake), **CSV** (simple, fragile).
**Watch out:** Schema evolution rules (adding optional fields is safe; renaming or reusing field numbers is not) matter more than the format.

### CORS
`working` · Related: HTTP basics, API gateway
**What:** Cross-Origin Resource Sharing: the browser rule that blocks a web page on origin A from reading responses from API origin B, unless B returns headers (`Access-Control-Allow-Origin` and others) allowing it. Non-simple requests trigger a **preflight** `OPTIONS` request.
**Watch out:** CORS protects *browsers'* users. It isn't API security, because servers and scripts ignore it. Configure it on the gateway or the service, and never use `*` with credentials.

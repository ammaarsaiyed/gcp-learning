# End-to-end journeys: watching the pieces work together

Each journey follows **one thing** (a request, an identity, a piece of data, a deployment, a failure, an agent's task) through a whole architecture, step by step. Every step names the concepts involved, so you can see how networking, identity, data, security and operations interlock in a real flow.

In the [practice app](../app/index.html#architect) each journey plays over its diagram, highlighting the components involved at each step. The format below is also what the app reads: `- node,node | step text`.

---

## Journey: A customer adds a payee and pays (the request path)
id: j-request
arch: mobile-banking-api
lesson: One tap touches DNS, anycast, TLS, WAF, OAuth, IAM, caching, transactions, idempotency and async events. The synchronous path is kept short, and everything that can wait is pushed onto Pub/Sub.
steps:
- app,lb | **Name to IP, then the nearest edge.** The app resolves `api.bank.co.uk` through DNS to the load balancer's single **anycast** IP. The internet routes the packets to the nearest Google edge location, so the **TCP and TLS handshakes** complete close to the user (2 short round trips instead of 2 long ones). The edge presents the bank's certificate (Certificate Manager), and an **SSL policy** enforces TLS 1.2+.
- lb,armor | **Edge security before anything else.** The global external Application Load Balancer evaluates the **Cloud Armor** policy attached to the backend service: OWASP rules (SQL injection, XSS), rate limits per client, and Adaptive Protection against L7 DDoS. Bad traffic is dropped at Google's edge and never reaches your project. This is *north-south* traffic crossing the outermost trust boundary.
- lb,apigee | **API management.** The request reaches Apigee (through PSC from the load balancer). Apigee **validates the OAuth access token** the app got at login (its signature, expiry and scopes), applies the app's **quota and spike arrest**, runs threat protection on the JSON, and records analytics. A request with a stolen but expired token fails here with 401. A valid token without the `payments:write` scope gets 403.
- apigee,bff | **Into the service, with identity.** Apigee calls the Cloud Run backend-for-frontend with a Google-signed **ID token** (audience = the service URL). Cloud Run checks the caller has `roles/run.invoker`. The Cloud Run service itself runs as its own **service account**, the identity it will use for every downstream call. Cloud Run scales instances based on **concurrency**, which matters on payday mornings.
- bff,cache | **Cheap reads first.** The payee list and product data are read **cache-aside** from Memorystore: on a miss, read Spanner and fill the cache with a TTL. The cache is an optimisation, not a dependency. If Memorystore is down, the service reads Spanner directly (slower, still correct).
- bff,ledger | **The part that must be right: a transaction.** Adding the payee and creating the payment happen in one **ACID transaction** in Spanner, together with an **idempotency key** row. If the app times out and retries, the second request finds the key and returns the original result, so there's no double payment. Spanner's synchronous replication means the commit survives a zone loss (multi-region config: a region loss too) with **RPO 0**.
- bff,events | **Everything else happens later.** After commit, the service publishes `PaymentCreated` to Pub/Sub (ideally through a **transactional outbox** or Spanner change stream, so the event can't be lost if the process crashes between commit and publish). The response goes back to the app now. The user isn't kept waiting for notifications or fraud analytics.
- events,notify | **Fan-out, at least once.** The push subscription delivers the event to the notification function. Delivery is **at-least-once**, so the function is **idempotent** (keyed on the payment ID), so a duplicate never sends two push notifications. Failures retry with backoff and land on a **dead-letter topic** after N attempts, which raises an alert. Other subscriptions (fraud, analytics) receive their own copies independently.

## Journey: Who is calling? (identity from login to database)
id: j-identity
arch: rag-policy-assistant
lesson: Identity changes form at every boundary: SSO session → IAP JWT → service account token → database IAM login. Each hop is authenticated and logged, nothing uses a stored password or key, and the user's own permissions still limit what they can retrieve.
steps:
- staff,iap | **Human identity, verified by the corporate IdP.** A colleague opens the assistant. IAP redirects them to sign in (federated to Entra ID or Okta through SAML/OIDC, with MFA). **Access Context Manager** checks the device is bank-managed. IAP then checks IAM (`iap.httpsResourceAccessor` granted to the right group). Without the device or the group, they never reach the app. This is zero trust: network location grants nothing.
- iap,app | **Identity passed on, signed.** IAP forwards the request with a signed JWT header (`x-goog-iap-jwt-assertion`) carrying the user's identity. The Cloud Run app **verifies the JWT** (signature, audience) instead of trusting a plain header, and extracts the user's email and groups. That's who the *person* is.
- app,vec | **Retrieval as the user, not as the app.** The app's **service account** connects to AlloyDB with IAM database authentication (no password). The vector query includes a **metadata filter on the user's groups**, so chunks from documents they aren't entitled to are never retrieved. The app is trusted to enforce document ACLs, so this filter is a control that gets tested.
- app,armor | **Screening before the model.** The prompt plus retrieved chunks go through Model Armor (prompt injection, jailbreak and sensitive-data checks). This is a trust boundary: everything retrieved is treated as *untrusted data*, not instructions.
- armor,llm | **Workload identity to Google APIs.** The app calls Gemini on Agent Platform. The client library uses **Application Default Credentials**: it asks the Cloud Run **metadata server** for a short-lived **access token** for the app's service account, which needs `roles/aiplatform.user`. The call is inside the **VPC-SC perimeter**, and it appears in **Data Access audit logs** as the service account.
- app,obs | **Attribution end to end.** The trace and structured logs record the user ID (from the IAP JWT), the service account, the document IDs retrieved and the model version. An auditor can answer "who asked what, what did they see, and which documents informed the answer?" without the logs holding full PII.

## Journey: From core banking to a regulator's report (the data path)
id: j-data
arch: cdc-lakehouse
lesson: Data changes shape and audience at each stage. Classification, residency, lineage and quality controls travel with it, which is what makes the final number defensible.
steps:
- core,ds | **Capture without hurting the source.** Datastream reads Oracle's **redo logs** (change data capture) over private connectivity. There are no heavy queries on the core system, and every insert, update and delete is captured in order.
- ds,raw | **Land raw, in the right place.** Changes stream into BigQuery bronze tables in `europe-west2`, in a project inside the **VPC-SC perimeter**, encrypted with **CMEK**. Raw tables are restricted to the data engineering group, because they contain raw PII.
- sdp,raw | **Know what you hold.** Sensitive Data Protection **discovery** profiles the tables and tags columns that contain names, account numbers or addresses. Those tags drive the masking rules in the next layers. This is classification as an automated control, not a spreadsheet.
- raw,dform | **Transform as code.** Dataform SQL (in git, reviewed, tested with **assertions**) cleans, deduplicates and models the data into silver and gold. PII columns are tokenised or dropped for wider audiences. Failed assertions stop the pipeline instead of publishing bad numbers.
- dform,gold | **Curated and governed.** Gold tables carry **policy tags** (column-level security with dynamic masking) and **row-level security** (for example by business unit). Analysts see masked values unless they're in the privileged group. **Partitioning and clustering** keep queries cheap.
- plex,gold | **Lineage and quality as evidence.** Dataplex records column-level **lineage** from the Oracle source through every transformation, plus data-quality scan results. When a regulator asks "where does this capital number come from?", the answer is a graph, not tribal knowledge (BCBS 239).
- gold,looker | **One definition of each metric.** Looker's semantic layer defines "active customer" and "arrears balance" once, so every dashboard and report agrees. Access is via groups, and every query is logged.
- gold,bqml | **Models next to the data.** BigQuery ML trains a propensity model on gold data without exporting it. The model and its training data snapshot are recorded for **model risk** (inventory, validation, monitoring).

## Journey: A zone fails, then a region fails (the failure path)
id: j-failure
arch: three-tier-ha
lesson: High availability is automatic and inside a region. Disaster recovery is a decision and a procedure across regions. Each tier must survive independently, or the weakest tier sets the availability.
steps:
- elb,web | **Zone B goes dark.** The load balancer's **health checks** fail for web VMs in zone B within seconds, and traffic shifts to zones A and C. Users with in-flight requests may see errors, and retries succeed. Because the managed instance group is **regional** with N+1 capacity, the remaining zones absorb the load, and the **autoscaler** adds VMs in healthy zones if CPU rises.
- web,ilb | **The same story one tier down.** The internal load balancer stops sending to app-tier VMs in zone B. **Autohealing** tries to recreate failed VMs, in the healthy zones if the zone stays down.
- ilb,appt | **Capacity check.** This is where N+1 planning matters: if each zone ran at 60% at peak, losing one zone pushes the others to 90%. The team had sized for 3 zones at 45% peak, so the system stays within SLO.
- appt,sql | **Database failover.** Zone B held the Cloud SQL primary. Cloud SQL HA detects the failure and **fails over to the standby** in zone A, which has every committed transaction (synchronous replication, **RPO 0**) after about a minute of unavailability. The app's connection pool reconnects, with **retries with backoff** on its side. Total impact: about a minute of errors on writes, within the 99.9% budget.
- sql,replica | **Now the region fails.** The whole of `europe-west2` is unavailable. HA can't help, because the standby was in the same region. The incident lead invokes the **DR plan**: promote the **cross-region read replica** to primary. Replication was asynchronous, so up to a few seconds of the last transactions may be missing (**RPO > 0**): the business accepted this in the impact-tolerance analysis, and reconciliation procedures exist.
- elb,web | **Bring up compute in the DR region.** Terraform (already tested) creates MIGs in the DR region from the same instance templates and images, and quotas there were **pre-raised**. The global load balancer gets the new backends. Users reconnect to the same anycast IP. Measured end to end, this takes 40 minutes against a 2-hour impact tolerance, and it was proven in last quarter's DR test, not assumed.
- nat,iap | **Don't forget the supporting cast.** Cloud NAT, IAP access, secrets, KMS keys, DNS and monitoring must all exist and work in the DR region too. Most failed DR tests fail on these "small" dependencies, not on the database.

## Journey: A code change reaches production (the deployment path)
id: j-deploy
arch: secure-cicd
lesson: The management plane is where risk concentrates. Every step replaces trust in people and keys with verifiable evidence: provenance, scans, attestations, approvals, and automatic rollback on SLO burn.
steps:
- dev,gh | **Change is proposed and reviewed.** A pull request gets peer review and automated checks (unit tests, linters, SAST, secret scanning). Branch protection means nobody, admins included, pushes straight to main.
- wif,build | **The pipeline authenticates without secrets.** Cloud Build (or GitHub Actions) gets credentials through **Workload Identity Federation**, restricted by attribute conditions to this repo and branch. There's no service account key to leak. The build runs in a **private pool** inside the bank's VPC, with no general internet access.
- build,ar | **Build once, with provenance.** The image is built once, pushed to Artifact Registry by **digest**, and Cloud Build records **SLSA provenance** (what source, which builder, which steps). Dependencies came through Artifact Registry remote repositories, a controlled, scanned proxy of public registries.
- ar,scan | **Gate on vulnerabilities.** Artifact Analysis scans the image. A critical CVE without an approved exception stops promotion. The SBOM is stored with the image.
- ar,deploy | **Promote the same artifact.** Cloud Deploy creates a release pointing at the digest and promotes it dev → test → prod. Production requires an **approval** from someone other than the author (**separation of duties**). Every promotion is recorded.
- deploy,prod | **Canary, then decide with data.** In prod, 10% of traffic goes to the new revision. Verification checks **SLO burn rate** and error rates for 30 minutes. If the burn rate spikes, Cloud Deploy **rolls back** automatically. Otherwise it promotes to 100%.
- binauthz,prod | **The last line of defence.** At admission, **Binary Authorization** verifies that the image has valid provenance and attestations from the bank's pipeline. Even an engineer with deploy permissions can't run an image built on their laptop. Break-glass exists, and every use alerts the security team.
- sm,prod | **Runtime configuration, not baked in.** Secrets are mounted from Secret Manager at deploy time, with versions pinned. The same image runs in every environment with different configuration. Rotating a secret means a controlled redeploy, not a rebuild.

## Journey: "Freeze my card and tell me about remortgaging" (an agent's task)
id: j-agent
arch: agentic-servicing
lesson: An agent turns one message into many model calls, tool calls and delegations. Each one needs identity, limits, screening and a trace, and real-world actions need explicit confirmation.
steps:
- cust,gw | **Authenticated entry and budget.** The customer's chat message arrives with their session token. Apigee verifies it, applies **token-based quotas** for the channel (a cost and abuse control), and logs the call. The gateway is also where a future model or provider switch happens without touching the app.
- gw,agent | **Session and memory.** Agent Runtime loads the conversation **session** (recent turns, state such as the selected card) and relevant long-term **memory** (for example "prefers text, not calls"). Memory holds personal data, so it has retention limits and is covered by the DPIA.
- agent,armor | **Screen the input.** Model Armor checks the message for prompt injection and sensitive data. The agent also treats **every tool result as untrusted** and screens it too, because indirect injection usually arrives through data, not the user.
- agent,llm | **Plan.** Gemini, with the orchestrator's instructions and tool declarations, decides on two sub-tasks: (1) freeze the card, which needs the `freeze_card` tool and confirmation; (2) remortgaging information, which belongs to the mortgage domain.
- agent,mcp | **Act, with confirmation and least privilege.** Before calling `freeze_card`, the agent asks "Freeze card ending 1234?" and waits for "yes". It then calls the MCP server. The MCP server validates the input against a strict schema and calls the card API using **its own service account**, which can freeze cards and nothing else. A prompt-injected "refund £5,000" has no tool to use.
- mcp,core | **Into the system of record.** The card API on-prem is reached privately, over Interconnect. The call carries a correlation ID, so the core system's audit log links back to this conversation.
- agent,a2a | **Delegate instead of duplicating.** For remortgaging, the orchestrator finds the mortgage team's agent from its **Agent Card** and sends an **A2A task**. The mortgage agent runs its own RAG over approved product documents and returns an artifact with cited content. Each team owns and validates its own agent.
- agent,human | **Know when to stop.** If confidence is low, the customer is vulnerable (Consumer Duty), or they ask for a person, the agent escalates to a human with a summary, instead of improvising.
- agent,trace | **Everything is a span.** Each model call, tool call, A2A delegation and confirmation is recorded in a trace. Offline, a sample of conversations is evaluated (task success, tool-call correctness, policy compliance) and the results feed model-risk monitoring.

## Journey: An on-prem app calls Gemini privately (the network path)
id: j-network
arch: private-gemini-onprem
lesson: "Private access" is three things that must all line up: DNS returns a private IP, routing knows how to reach it, and the perimeter admits the caller. Miss one and traffic silently goes over the internet or fails.
steps:
- app,odns | **It starts with DNS.** The on-prem app calls `europe-west2-aiplatform.googleapis.com`. Its resolver is the corporate DNS, which has a **conditional forwarder** for `googleapis.com` pointing at Google Cloud.
- odns,inbound | **Across to Cloud DNS.** The forwarder sends the query over the Interconnect to the **inbound server policy** IP in the hub VPC (a Cloud DNS entry point for on-prem resolvers).
- inbound,pzone | **The split-horizon answer.** A Cloud DNS **private zone** for `googleapis.com` answers with the **PSC endpoint's internal IP** instead of public Google IPs. Outside the bank, the same name resolves to public addresses. Inside, it resolves to the private path.
- app,ic | **The packets take the private road.** The app opens a TLS connection to that internal IP. On-prem routers know the route because Cloud Router **advertised the PSC endpoint's IP range over BGP**.
- ic,cr | **BGP keeps it dynamic.** The redundant VLAN attachments (99.99% topology) each have BGP sessions. If one circuit fails, BFD detects it in under a second, and traffic moves to the remaining paths.
- cr,psc | **The PSC endpoint.** Traffic arrives at the PSC endpoint, a forwarding rule in the VPC that fronts Google APIs (configured for the VPC-SC-compatible APIs bundle). TLS still terminates at Google with the real `googleapis.com` certificate, so certificate checks pass.
- perim,gem | **The perimeter decides.** The AI project is in a **VPC-SC perimeter**. The request carries the app's identity (a federated or service account token) and comes from on-prem ranges allowed by an **access level** in an **ingress rule**. Calls from anywhere else, even with valid tokens, are blocked. If any of DNS, routing or perimeter is wrong, you get either public-internet traffic or a VPC-SC "request violates perimeter" error, which is the first thing to check when it breaks.
- psc,gem | **The call itself.** Gemini processes the request in the regional endpoint (`europe-west2` processing for supported models), and it's recorded in Data Access audit logs. The response returns along the same path.

## Journey: Scoring a card payment in under 100 ms (a latency budget)
id: j-latency
arch: realtime-fraud
lesson: Hard latency targets are met by budgeting every hop and keeping slow work off the hot path. Freshness (streaming features) and accountability (analytics, monitoring) run asynchronously alongside.
steps:
- switch,api | **The budget.** The scheme gives the bank about 100 ms to decide. Budget: about 5 ms network to GCP over Interconnect, 10 ms service overhead, 15 ms feature lookup, 30 ms model, about 40 ms spare for tail latency. The scoring service runs with **min instances** (no cold starts) and **connection reuse** (no repeated TLS handshakes).
- api,feat | **Features in single-digit milliseconds.** One Bigtable read by row key (card hash) returns the precomputed features: spend in the last 10 minutes and 24 hours, merchant novelty. Row key design avoids hotspots and puts everything for a card in one row.
- api,model | **Prediction.** The fraud model (gradient-boosted trees) on an online endpoint, reached privately, returns a score in about 10–20 ms. A **timeout** with a fallback rule set (for example "approve under £30, decline over £5k unless whitelisted") means a slow model never blocks payments: **graceful degradation**.
- api,bus | **Respond first, record after.** The decision returns to the switch. Asynchronously, the transaction and decision are published to Pub/Sub, so nothing on the hot path waits for analytics.
- bus,flow | **Keep features fresh.** Dataflow consumes the stream, computes **windowed aggregates** by event time (watermarks handle late events), and writes them back to Bigtable within seconds. The next transaction on the same card sees updated features.
- bus,bq | **The record of every decision.** A BigQuery subscription stores every event for investigations, retraining and audit.
- bq,mon | **Watch the model.** Model monitoring compares live feature and score distributions with the training baseline. **Drift** alerts go to the model owner and model risk, because a fraud model degrades as fraudsters adapt.
- bq,looker | **Close the loop with people.** Fraud ops dashboards show decline rates and false positives. Confirmed fraud labels flow back into training data. That's the feedback loop that keeps the system improving.

## Journey: One outbound call, fully controlled (the egress path)
id: j-egress
arch: controlled-egress
lesson: Egress control is layered. The default is deny, there's one approved exit, the destination is checked by name, the source IP is fixed and known, and every request is logged.
steps:
- svc,dve | **No direct route out.** The payments adapter has internal-only ingress, and **all egress** is sent through Direct VPC egress into the subnet. Without that setting, Cloud Run would use Google's default internet egress and bypass every control below.
- fwp,dve | **Default deny.** A firewall policy on the subnet denies all egress except to the Secure Web Proxy. A compromised container can't reach an attacker's server directly.
- dve,swp | **Checked by name.** The service sends its request through Secure Web Proxy, whose policy says this service account may reach `api.paymentscheme.com` and nothing else. The proxy logs the request (source identity, host, result). An exfiltration attempt to another host is denied and logged.
- cert,svc | **Prove who you are.** The scheme requires **mTLS**. The service mounts its client certificate and key from Secret Manager (access audited, expiry tracked), and the TLS handshake presents it.
- swp,nat | **A predictable source.** Cloud NAT translates to **manually reserved static IPs**, which the scheme has on its allow-list. Changing them is a coordinated change with the partner, not an accident.
- nat,scheme | **The call completes.** The scheme verifies the source IP and the client certificate, and the bank verifies the scheme's server certificate. The response returns through NAT's connection tracking. Nothing on the internet can start a connection inward.

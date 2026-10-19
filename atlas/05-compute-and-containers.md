# 05 · Compute, containers and runtimes

Where code runs, how it scales, and what you're responsible for at each level.

---

### Virtualization and the hypervisor
`working` · Related: Compute Engine, Containers
**What:** A **hypervisor** runs several isolated virtual machines on one physical host, each with its own kernel and OS. It gives strong isolation, and VMs boot in tens of seconds.
**GCP:** Compute Engine runs on a KVM-based hypervisor with hardware offload (Titanium). **Live migration** moves running VMs between hosts during maintenance without rebooting them (except GPU and some specialized VMs, which stop for maintenance).

### Compute Engine (VMs)
`core` · Related: Machine families, Persistent Disk, Managed Instance Groups
**What:** IaaS virtual machines. You choose CPU, memory, disk, image, network and service account, and you own the OS and everything above it.
**How:** Zonal resource. Key settings: machine type, boot image, disks, network interfaces (multi-NIC for appliances), service account + access scopes, metadata (startup scripts, OS Login), availability policy (live migrate or terminate on maintenance, automatic restart), **sole-tenant nodes** (dedicated hosts for licensing or isolation), reservations.
**GCP:** Use it for lift-and-shift, commercial software that needs a VM, licensing-bound workloads, special hardware, or anything needing kernel or OS control.

### Machine families
`working` · Related: Compute Engine, GPUs and TPUs
**What:** Families tuned for different workloads. **General purpose:** E2 (cost-optimised), N2/N2D/N4 (balanced), C4A/T2A (Arm). **Compute-optimised:** C3/C4, H3. **Memory-optimised:** M3/M4 (SAP HANA, huge in-memory DBs). **Accelerator-optimised:** A3/A4 (NVIDIA H100/H200/B200), G2 (L4 GPUs). **Storage-optimised:** Z3. **Custom machine types** let you pick exact vCPU and memory (E2/N-series).
**Watch out:** Not every family is in every zone. Check availability in europe-west2 early for GPUs.

### Persistent Disk, Hyperdisk and Local SSD
`working` · Related: Block storage, Snapshots
**What:** Block storage for VMs. **Persistent Disk** (pd-standard, pd-balanced, pd-ssd) is durable, network-attached, zonal or **regional** (synchronously replicated across two zones for HA). **Hyperdisk** is the newer generation, with performance (IOPS and throughput) provisioned separately from capacity. **Local SSD** is physically attached, very fast, and **ephemeral**: the data is lost when the VM stops or is deleted.
**Watch out:** Never keep anything you can't lose on Local SSD.

### Images, snapshots, machine images and instance templates
`working` · Related: Compute Engine, Managed Instance Groups, Backup and PITR
**What:** **Image:** a bootable disk template (public images, or your own "golden" hardened images, often built with Packer). **Snapshot:** an incremental, point-in-time backup of a disk, stored regionally or multi-regionally, and schedulable. **Machine image:** a whole VM (config + all disks) for cloning or backup. **Instance template:** an immutable VM configuration used by MIGs.
**GCP:** Banks typically maintain hardened golden images (CIS benchmarks), restrict which images can be used with the org policy `compute.trustedImageProjects`, and use snapshot schedules for backups.

### Managed Instance Groups (MIGs)
`core` · Related: Autoscaling, Health checks, Cloud Load Balancing
**What:** A fleet of identical VMs created from an instance template and managed as one.
**How:** **Autoscaling** (on CPU, load-balancer serving capacity, Cloud Monitoring metrics, or schedules), **autohealing** (recreates VMs that fail an application health check), **rolling updates** and canaries (`max surge` / `max unavailable`), **regional MIGs** (spread across zones for HA), stateful MIGs (keep disks and IPs for stateful apps).
**GCP:** The VM equivalent of a Kubernetes Deployment. It's the backbone of lift-and-shift HA designs behind load balancers.

### Spot VMs
`core` · Related: Pricing models, Batch, GKE node pools
**What:** Spare capacity at a large discount (often 60–91% off) that Google can **reclaim at any time**, with a 30-second warning. No minimum or maximum runtime. (Preemptible VMs were the older version, limited to 24 hours.)
**GCP:** Good for fault-tolerant batch work, CI runners, stateless GKE node pools, rendering, and some ML training with checkpointing. Never for databases or anything that can't tolerate sudden loss.

### GPUs and TPUs
`working` · Related: Machine families, AI Hypercomputer, Training vs inference
**What:** **GPUs** (NVIDIA L4, A100, H100/H200, B200…) are general accelerators for ML training and inference, graphics and simulation. **TPUs** are Google's custom ML accelerators (v5e, v5p, v6e Trillium and newer), very efficient for large-scale training and serving, especially with JAX or TensorFlow and increasingly PyTorch.
**How:** Attached to VMs, GKE node pools, Cloud Run (GPUs), and the AI platform's training and prediction. Capacity is scarce: use **reservations**, **Dynamic Workload Scheduler** (queue for capacity, flex-start) or committed use.
**Watch out:** Most bank GenAI work *consumes* hosted models (Gemini, Claude through Model Garden) and needs no GPUs. GPUs matter when you self-host open models or fine-tune.

### Containers
`core` · Related: Container images, Kubernetes, Cloud Run
**What:** A process (or a few) isolated using kernel features: **namespaces** (its own view of processes, network and filesystem) and **cgroups** (CPU and memory limits), packaged with everything it needs to run. They share the host kernel, so they're lighter and start faster than VMs, but isolation is weaker.
**How:** Build once, run anywhere: the same image runs on a laptop, Cloud Run, GKE or another cloud, which is why containers count as a portability and exit-strategy lever.
**GCP:** Cloud Run adds a gVisor sandbox (gen1) or a microVM (gen2 execution environment) for stronger isolation. GKE Sandbox (gVisor) is available for untrusted workloads.

### Container images and registries
`core` · Related: Artifact Registry, Binary Authorization, Software supply chain security
**What:** An image is a stack of read-only **layers** plus metadata (entrypoint, env), following the **OCI** standard. It's referenced by **tag** (`:v1.2`, mutable) or **digest** (`@sha256:…`, immutable).
**GCP:** **Artifact Registry** stores container images and language packages (Maven, npm, Python, Go, apt/yum), regional or multi-regional, with IAM, vulnerability scanning, cleanup policies, and remote/virtual repositories (proxy and cache public registries such as Docker Hub and PyPI, important for controlled egress in banks).
**Watch out:** Deploy by **digest** for reproducibility. Tags can be moved to point at different content.

### Kubernetes architecture
`core` · Related: GKE, Pods, Deployments, Services
**What:** An open-source system for running containers across a cluster of machines, using **declarative desired state** and continuous reconciliation.
**How:** **Control plane:** the **API server** (everything goes through it), **etcd** (the state store), the **scheduler** (places Pods on nodes), **controllers** (loops that drive actual state towards desired state). **Nodes:** the **kubelet** (runs Pods), a container runtime (containerd), kube-proxy or eBPF (Service networking). You `kubectl apply` YAML manifests and controllers make it so.
**GCP:** GKE runs the control plane for you (and, in Autopilot, the nodes too).

### Pods, ReplicaSets and Deployments
`core` · Related: Kubernetes architecture, Services, Autoscaling
**What:** A **Pod** is the smallest deployable unit: one or more containers sharing a network namespace (one IP) and volumes, scheduled together. A **ReplicaSet** keeps N identical Pods running. A **Deployment** manages ReplicaSets to give declarative **rolling updates** and rollbacks.
**Watch out:** Pods are disposable. They get new IPs when recreated, which is why Services exist.

### Kubernetes Services
`core` · Related: Pods, GKE networking, Service discovery
**What:** A stable virtual IP and DNS name in front of a changing set of Pods (selected by labels).
**How:** Types: **ClusterIP** (internal only, the default), **NodePort** (a port on every node), **LoadBalancer** (provisions a cloud load balancer; on GKE an L4 passthrough NLB, internal or external), **Headless** (no virtual IP; DNS returns the Pod IPs, used with StatefulSets).
**GCP:** For HTTP(S), use **Gateway API** or Ingress on top of Services, which provisions Application Load Balancers with container-native NEGs.

### Ingress and Gateway API
`working` · Related: Kubernetes Services, Cloud Load Balancing, Ingress and egress
**What:** Kubernetes APIs for **L7 routing into the cluster**. **Ingress** is the older, limited API. **Gateway API** is the newer, role-oriented one: *GatewayClass* (infrastructure provider), *Gateway* (owned by the platform team), *HTTPRoute* (owned by app teams), with traffic splitting, header matching and cross-namespace routing.
**GCP:** The GKE Gateway controller provisions global or regional, external or internal Application Load Balancers from Gateway resources. It supports multi-cluster Gateways for multi-region.

### StatefulSets, DaemonSets, Jobs and CronJobs
`working` · Related: Pods, Persistent volumes
**What:** **StatefulSet:** Pods with stable identities (`db-0`, `db-1`) and their own persistent volumes, for databases and quorum systems. **DaemonSet:** one Pod per node (log agents, security agents). **Job:** run to completion. **CronJob:** scheduled Jobs.
**Watch out:** Running databases on Kubernetes is possible but operationally heavy. Banks usually prefer managed databases.

### ConfigMaps and Kubernetes Secrets
`working` · Related: Secret Manager, Workload Identity Federation for GKE
**What:** **ConfigMaps** inject non-secret configuration. **Secrets** inject sensitive values, but they're only base64-encoded, and stored in etcd (encrypted at rest on GKE, with optional application-layer encryption using Cloud KMS).
**GCP:** Prefer **Secret Manager**, accessed through Workload Identity or the Secret Manager CSI driver / add-on, so secrets have central IAM, audit and rotation.

### Namespaces, resource requests and limits
`working` · Related: GKE Autopilot, Autoscaling
**What:** **Namespaces** divide a cluster for teams or environments (scoping RBAC, quotas and network policies). **Requests** are what a Pod is guaranteed and scheduled on. **Limits** are the maximum it may use (exceeding the memory limit gets the container OOM-killed; CPU is throttled).
**GCP:** GKE Autopilot **bills by Pod requests**, so right-sizing requests is cost control.

### Autoscaling: HPA, VPA, cluster autoscaler
`working` · Related: Autoscaling concepts, Managed Instance Groups, Cloud Run
**What:** **Horizontal Pod Autoscaler (HPA):** changes the replica count based on CPU, memory or custom/external metrics (for example Pub/Sub backlog). **Vertical Pod Autoscaler (VPA):** recommends or sets requests. **Cluster autoscaler / node auto-provisioning:** adds or removes nodes when Pods can't be scheduled or nodes sit idle.
**Watch out:** HPA and VPA acting on the same metric for the same Pods fight each other.

### Probes: liveness, readiness and startup
`working` · Related: Health checks, Pods
**What:** **Readiness:** is the Pod ready for traffic? (Failing removes it from Service endpoints.) **Liveness:** is it stuck? (Failing restarts the container.) **Startup:** give slow starters time before liveness checks begin.
**Watch out:** A liveness probe that checks a database restarts all your Pods when the database blips, turning a partial outage into a full one.

### GKE Standard vs Autopilot
`core` · Related: Kubernetes architecture, Spot VMs
**What:** **Autopilot:** Google manages the nodes, scaling, security hardening and upgrades. You deploy Pods and pay for their requested resources. This is the default recommendation. **Standard:** you manage node pools (machine types, GPUs, autoscaling, upgrades) and pay per node.
**How:** Both have a Google-managed control plane with an SLA. Both support **regional** clusters (control plane and nodes across 3 zones), **release channels** (Rapid, Regular, Stable, Extended) and maintenance windows and exclusions.
**GCP:** Choose Standard when you need node-level control: specific GPUs or TPUs, special kernels, privileged DaemonSets, or bin-packing tuned for cost.

### Service mesh and sidecars
`working` · Related: mTLS, Zero trust, Observability
**What:** An infrastructure layer for service-to-service traffic. A proxy (usually **Envoy**) sits beside each workload as a **sidecar**, or as a node-level or ambient proxy, and handles **mTLS**, retries, timeouts, traffic splitting and authorization policies, and produces uniform telemetry, without code changes. **Istio** is the main open-source mesh.
**GCP:** **Cloud Service Mesh** (managed Istio / Traffic Director) for GKE, VMs and Cloud Run. It gives automatic workload identity certificates, SLO-ready golden-signal metrics, and authorization policies like "only payments-api may call ledger-api".

### Helm, Kustomize and fleets
`aware` · Related: GitOps, Infrastructure as code
**What:** **Helm:** a package manager for Kubernetes (templated "charts"). **Kustomize:** template-free overlays per environment. **Fleets (GKE Enterprise):** manage many clusters as one: Config Sync (GitOps), Policy Controller (OPA Gatekeeper constraints), multi-cluster ingress or gateway, and Cloud Service Mesh.

### Cloud Run services
`core` · Related: Serverless, Cold starts, Concurrency, Serverless VPC Access
**What:** Fully managed, request-driven containers. Give it an image (or source), and it serves HTTPS with autoscaling, including **to zero**.
**How:** Key concepts: **revisions** (immutable code + config) and **traffic splitting** across them with tags; **concurrency** (requests per instance, default 80, up to 1000); **min/max instances**; **CPU allocation** (request-based, or instance-based "always on"); request **timeout** up to 60 minutes; **startup CPU boost**; **gen2 execution environment** (full Linux compatibility, network file systems); multi-container **sidecars**; **volume mounts** (Cloud Storage FUSE, NFS, in-memory, secrets); **GPUs**; **ingress settings** (all / internal / internal + load balancer); IAM authentication (`roles/run.invoker`); **Direct VPC egress**; HTTP/2 and gRPC, WebSockets and server-sent events; **service identity** (its service account); regional deployment (use a load balancer for multi-region).
**GCP:** The default runtime for APIs, web apps, AI agents and backends-for-frontends. Common in bank GenAI stacks for orchestrators, tools and MCP servers.

### Cloud Run jobs and worker pools
`working` · Related: Batch, Cloud Scheduler, Workflows
**What:** **Jobs:** containers that run to completion, with parallel **tasks** (each gets an index), retries, and up to days of runtime. Used for batch, ETL, migrations and scheduled work through Cloud Scheduler. **Worker pools:** always-on, non-HTTP background workers (for example pulling from Pub/Sub or Kafka).

### Cloud Run functions
`working` · Related: Eventarc, Serverless
**What:** Functions-as-a-service (formerly Cloud Functions, now built on Cloud Run). Write a function, and it's triggered by HTTP or by events (Pub/Sub, Cloud Storage, Firestore, audit-log events through Eventarc).
**GCP:** Good for small glue code. Anything bigger or longer-lived fits better as a Cloud Run service.

### Cold starts
`core` · Related: Cloud Run services, Autoscaling concepts
**What:** Extra latency when a new instance has to start (pull the image, start the runtime, run initialization) before serving a request. It happens when scaling from zero or during sharp scale-out.
**How:** Mitigations: **min instances** (always-warm capacity, which you pay for), smaller images, lazy initialization, startup CPU boost, language and runtime choice (Go is faster than JVM without tuning), and connection reuse.
**Watch out:** Large Python AI images (with torch, for example) can take tens of seconds to cold start. Keep heavy model work in hosted endpoints.

### Concurrency (requests per instance)
`core` · Related: Cloud Run services, Cold starts
**What:** How many requests one instance handles at the same time. A higher setting means fewer instances and lower cost, but the code must be thread-safe or async and stay within per-instance memory.
**Watch out:** LLM-calling services are I/O-bound (they wait on the model), so high concurrency with async code is very efficient. CPU-bound work (local inference, PDF parsing) needs low concurrency.

### Serverless
`core` · Related: Cloud Run, BigQuery, Pub/Sub, Firestore
**What:** No servers to provision or manage, automatic scaling (often to zero), and paying for use rather than capacity.
**GCP:** Compute (Cloud Run, functions), data (BigQuery, Firestore, Spanner with autoscaling), messaging (Pub/Sub, Eventarc), orchestration (Workflows), AI (Gemini APIs).
**Watch out:** Serverless doesn't mean limitless. There are quotas, concurrency limits and downstream bottlenecks (databases) to plan for.

### Autoscaling concepts (horizontal vs vertical)
`core` · Related: Managed Instance Groups, HPA, Cloud Run services
**What:** **Horizontal** scaling adds or removes instances: needs stateless design, a load balancer, and has effectively no ceiling. **Vertical** scaling gives an instance more CPU and RAM: simple, limited by the largest machine, and often needs a restart.
**How:** Autoscalers act on signals (CPU, requests, queue depth, custom metrics), with cooldowns or stabilization to avoid flapping. Predictive autoscaling uses history.
**Watch out:** Scaling the stateless tier just moves the bottleneck to the database. Design both tiers together.

### Stateless vs stateful services
`core` · Related: Autoscaling concepts, Cloud Run services, Caching
**What:** A **stateless** service keeps no client state between requests (state lives in a DB, cache or token), so any instance can serve any request, and scaling and failover are trivial. A **stateful** service keeps state locally (sessions in memory, local files, a database engine), which makes scaling, failover and deployment harder.
**Watch out:** Cloud Run instances can disappear at any time. Store conversation and agent session state in Firestore, Memorystore, AlloyDB or Agent Runtime sessions, never in instance memory.

### Twelve-factor app
`working` · Related: Stateless vs stateful services, Containers
**What:** Principles for cloud-native apps: config in the environment, backing services as attached resources, stateless processes, port binding, disposability (fast start, graceful shutdown on SIGTERM), dev/prod parity, logs as event streams to stdout, and more.
**GCP:** Cloud Run, GKE and Cloud Logging assume these principles.

### App Engine
`aware` · Related: Cloud Run services
**What:** Google's original PaaS (standard environment: sandboxed runtimes; flexible environment: containers on VMs). It still runs many legacy apps, but **Cloud Run is the recommended choice for new work**.

### Batch
`aware` · Related: Cloud Run jobs, Spot VMs
**What:** A managed batch scheduler that provisions VMs (including Spot and GPUs) to run containerized or script jobs at scale, then tears them down. Used for HPC, risk simulations and large data jobs.

### Google Cloud VMware Engine and Bare Metal Solution
`aware` · Related: Migration strategies (7 Rs)
**What:** **VMware Engine:** a dedicated VMware SDDC (vSphere, vSAN, NSX) running in Google Cloud, so VMware estates can be lifted without re-platforming. **Bare Metal Solution:** dedicated physical servers near Google regions for workloads like Oracle RAC that can't be virtualized or need special licensing.

### Developer environments (Cloud Shell, Cloud Workstations)
`aware` · Related: VPC Service Controls
**What:** **Cloud Shell:** a free, ephemeral browser terminal with tools pre-installed. **Cloud Workstations:** managed, policy-controlled dev environments running inside your VPC, which banks like because source code never sits on laptops and egress is controlled.

### VM Manager and patch management
`aware` · Related: Vulnerability management, Compute Engine
**What:** OS inventory, **patch compliance reporting**, scheduled patch jobs, and OS policies (config management) across VM fleets, through the OS Config agent.

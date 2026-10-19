# 02 · GCP networking

How Google implements the fundamentals from file 01. Most bank architecture reviews spend more time on this domain than on any other.

---

### Google's network, edge and Network Service Tiers
`working` · Related: Anycast, Cloud Load Balancing
**What:** Google runs a private global backbone with edge points of presence (PoPs) in many cities. **Premium Tier** (the default) carries your traffic on Google's backbone to the edge nearest the user. **Standard Tier** hands it to the public internet near your region: cheaper, slower, and regional only.
**How:** User requests reach the nearest edge, where **Google Front Ends (GFEs)** terminate TCP/TLS and apply load balancing and Cloud Armor. Traffic then crosses the backbone to your region.
**GCP:** Global load balancers require Premium Tier. Standard Tier suits cost-sensitive, single-region, internet-facing workloads.

### Andromeda (software-defined networking)
`aware` · Related: VPC network, Firewall
**What:** Google's network virtualisation stack. Your VPC, routes and firewall rules are programmed into the host each VM runs on. There are no physical routers or firewall boxes in your path.
**Why it matters:** It's why VPCs can be global, why firewall rules apply per NIC without choke points, and why broadcast and multicast don't work as they do on a physical LAN.

### VPC network
`core` · Related: Subnet, Routes, VPC firewall rules, Shared VPC
**What:** A Virtual Private Cloud is a private, isolated, software-defined network. **In GCP a VPC is global**: one VPC spans every region, with regional subnets. A project can hold several VPCs (default quota is 15).
**How:** VMs in different regions on the same VPC talk over internal IPs on Google's backbone with no extra setup. Isolation between VPCs is total unless you connect them (peering, Network Connectivity Center, VPN, PSC).
**GCP:** Modes are **auto** (one /20 per region, created automatically; this is the `default` network) and **custom** (you define the subnets). Use **custom mode** in production and delete the `default` network, or skip creating it with the `compute.skipDefaultNetworkCreation` org policy.
**Watch out:** A VPC belongs to one project. Sharing it across projects is what **Shared VPC** is for.

### Subnet (primary and secondary ranges)
`core` · Related: CIDR and subnetting, GKE networking, Private Google Access
**What:** A regional IP range inside a VPC. Resources in any zone of that region can use it.
**How:** The **primary range** holds VM NIC IPs and internal load balancer IPs. **Secondary ranges** are extra CIDRs on the same subnet, used as **alias IP ranges**, mainly for GKE Pods and Services. Private Google Access and flow logs are set per subnet. Special-purpose subnets exist too: **proxy-only subnets** (for regional Envoy-based load balancers) and **PSC NAT subnets**.
**Watch out:** Plan GKE ranges generously. Pod ranges get used up fast (each node reserves a block for its Pods).

### Internal and external IP addresses
`working` · Related: IP address, Cloud NAT
**What:** **Internal** IPs come from subnet ranges and are reachable inside the VPC (and connected networks). **External** IPs are internet-routable.
**GCP:** You can reserve static internal or external addresses. A **regional** external IP serves VMs and regional load balancers. A **global** external IP serves global load balancers. An unused reserved external IP is billed.
You can also **bring your own IP** ranges (BYOIP), so public addresses you own keep working after migration (useful when partners allow-list your IPs).
**Watch out:** The org policy `compute.vmExternalIpAccess` (deny all, or allow-list specific VMs) is a standard bank guardrail.

### VPC routes
`working` · Related: Routing and route tables, Cloud Router, Policy-based routes
**What:** Routes that decide where packets leave a VM's NIC. They are VPC-scoped and evaluated per VM.
**How:** Route types: **subnet routes** (automatic), **default route** (to the internet gateway, and deletable), **custom static routes** (can target only VMs with certain network tags), **dynamic routes** (learned through BGP by Cloud Router) and **policy-based routes** (match on source range, protocol or destination, and evaluated before normal routes, often used to steer traffic through firewall appliances). The most specific prefix wins, then priority.
**GCP:** Next hops include a VM, an internal passthrough Network Load Balancer (for highly available appliances), a VPN tunnel, an Interconnect attachment, or the default internet gateway.

### VPC firewall rules
`core` · Related: Firewall (stateful), Cloud NGFW, Health checks
**What:** Stateful rules on a VPC that allow or deny traffic to and from VM NICs.
**How:** Each rule has: **direction** (ingress or egress), **priority** (0–65535, lower wins), **action** (allow or deny), **targets** (all instances, network tags, or service accounts), **source/destination** (CIDRs, tags or service accounts), and **protocols/ports**. **Implied rules** are deny all ingress and allow all egress, at the lowest priority. Firewall Rules Logging records matches.
**GCP:** Target by **service account** rather than **network tag** where you can. Anyone who can edit a VM can change its network tags, but using a service account needs IAM permission (`iam.serviceAccountUser`).
**Watch out:** Load balancer health checks come from `35.191.0.0/16` and `130.211.0.0/22`. Forget to allow them and every backend shows as unhealthy.

### Cloud NGFW and firewall policies
`working` · Related: VPC firewall rules, Secure Tags, Secure Web Proxy
**What:** **Cloud Next Generation Firewall** is GCP's firewall service. Its policies come in three kinds: **hierarchical** (attached to the org or a folder), **global network** and **regional network** firewall policies.
**How:** Evaluation order: hierarchical policies (org → folder) → VPC firewall rules → global network policy → regional network policy (the order between VPC rules and network policies is configurable). A rule can **allow**, **deny** or **goto_next** (delegate to the next level). Tiers: **Essentials** (the basics, plus secure tags and address groups), **Standard** (adds FQDN objects, geolocation and threat-intelligence lists), **Enterprise** (adds L7 intrusion prevention with TLS inspection, using Palo Alto technology).
**GCP:** Banks use hierarchical policies for non-negotiables ("deny SSH from the internet everywhere"; "always allow the security scanner range") that project owners can't override.

### Secure Tags vs network tags vs labels
`working` · Related: Cloud NGFW, Labels, Org Policy
**What:** Three things that look similar. **Network tags** are plain strings on a VM, used by legacy firewall rules and routes, and anyone who can edit the VM can change them. **Secure Tags** (Resource Manager tags) are key/value pairs defined at the org or project level and governed by IAM, used in firewall policies, IAM conditions and org policy conditions. **Labels** are key/value metadata for cost allocation and filtering, with no security effect.
**Watch out:** Exam and interview favourite: "which of these can be used to enforce security?" Secure tags. Labels never.

### Network virtual appliances and multi-NIC routing
`working` · Related: VPC routes, Cloud NGFW, Load balancing
**What:** Third-party firewalls, IDS, SD-WAN or proxies (Palo Alto, Fortinet, Check Point…) running as VMs, often with **multiple NICs** (one per VPC), so traffic between VPCs or to on-prem is inspected as it passes through them.
**How:** For HA, put the appliances behind an **internal passthrough Network Load Balancer** and use it as a route's **next hop** (or use policy-based routes), so traffic fails over when an appliance dies. **Symmetric routing** matters: the return traffic must pass through the same appliance.
**GCP:** Common where bank security standards mandate a specific vendor's firewall. Cloud NGFW Enterprise and Network Security Integration (in-band or out-of-band inspection) are the managed alternatives.

### Cloud Router
`working` · Related: BGP, Cloud VPN, Cloud Interconnect, Cloud NAT
**What:** A fully distributed, managed BGP control plane for a VPC region.
**How:** It exchanges routes with on-prem routers over VPN tunnels or Interconnect VLAN attachments, using custom advertised prefixes, MED and BFD. It also holds the Cloud NAT configuration. Learned routes become dynamic routes in the VPC (regional or global, depending on the VPC's routing mode).

### Cloud NAT
`core` · Related: NAT, Private Google Access, Secure Web Proxy
**What:** Managed outbound NAT so resources without external IPs can reach the internet (patches, external APIs) while staying unreachable from it.
**How:** Configured on a Cloud Router per region. It's software-defined: Andromeda rewrites packets on each host, so there's no gateway VM and no bottleneck. NAT IPs are either auto-allocated or **manual** (so partners can allow-list them). Ports per VM are **static** or **dynamic** allocation. **Private NAT** translates between networks with overlapping ranges (for example Network Connectivity Center spokes).
**Watch out:** Cloud NAT only handles *outbound* connections and their replies. For inbound traffic, use a load balancer.

### Private Google Access (PGA)
`core` · Related: Private Service Connect, VPC Service Controls, Cloud NAT
**What:** Lets VMs with only internal IPs reach Google APIs (Cloud Storage, BigQuery, the AI platform…) without internet access.
**How:** Enabled per subnet. API traffic stays on Google's network. You can point DNS at special VIP ranges: `private.googleapis.com` (`199.36.153.8/30`, all APIs) or **`restricted.googleapis.com`** (`199.36.153.4/30`, only APIs that support VPC Service Controls, which helps enforce the perimeter). **PGA for on-premises hosts** extends this over VPN or Interconnect, by advertising those ranges through Cloud Router and setting up DNS.
**Watch out:** PGA isn't needed for serverless services. It's about VMs and GKE nodes calling Google APIs.

### Private Service Connect (PSC)
`core` · Related: Private Google Access, Private services access, Service attachment
**What:** Private, IP-based endpoints *inside your VPC* for Google APIs, Google-managed services, or services published by other teams or vendors.
**How:** **Consumer side:** a PSC *endpoint* (a forwarding rule with an internal IP in your subnet) or a *PSC backend* (behind your own load balancer). **Producer side:** a *service attachment* that publishes an internal load balancer for consumers to connect to. Traffic is NAT'd one way, so **overlapping IP ranges don't matter**, and the producer and consumer stay isolated (no route exchange, unlike peering). **PSC interfaces** let a producer reach back into a consumer VPC.
**GCP:** You can reach Cloud SQL, AlloyDB, Memorystore, the AI platform's endpoints (Gemini/Vertex), Apigee and third-party SaaS (for example Snowflake, MongoDB Atlas) privately through PSC. It's the modern answer to "private connectivity to managed services".

### Private services access (PSA)
`working` · Related: VPC Network Peering, Private Service Connect
**What:** The older way of privately reaching Google-managed services (Cloud SQL, Memorystore, Filestore, older AI endpoints): you allocate an IP range, and Google creates a **VPC peering** to the service producer's network.
**Watch out:** Because it's peering, it's **non-transitive**: on-prem can't reach a PSA-connected Cloud SQL through a peered VPC without exporting custom routes. PSC avoids these problems and is preferred for new designs.

### Serverless VPC Access and Direct VPC egress
`working` · Related: Cloud Run, Cloud NAT, Private services access
**What:** How serverless services (Cloud Run, Cloud Run functions, App Engine) send traffic *into* a VPC, for example to reach a private-IP database or on-prem.
**How:** **Serverless VPC Access connector:** managed connector VMs that forward traffic (older; costs money even when idle; throughput limits). **Direct VPC egress:** Cloud Run instances get IPs directly in your subnet (newer, faster, no connector). Either way you choose whether *all* egress or only *private ranges* go through the VPC. Sending all egress through the VPC is how you put Cloud Run behind Cloud NAT with fixed IPs, or behind on-prem egress controls.

### VPC Network Peering
`core` · Related: Shared VPC, Network Connectivity Center, Private services access
**What:** Connects two VPCs (same or different projects or orgs) so they exchange subnet routes and talk over internal IPs.
**How:** Both sides must create the peering. Subnet ranges **must not overlap**. Custom routes can be imported or exported. **It's not transitive**: if A peers with B and B with C, A still can't reach C. Each side keeps its own firewall and IAM administration.
**Watch out:** Peering meshes don't scale (quota limits, no transitivity). For hub-and-spoke designs use Network Connectivity Center or Shared VPC.

### Shared VPC
`core` · Related: VPC network, Landing zone, Separation of duties
**What:** One **host project** owns a VPC. Attached **service projects** create their resources (VMs, GKE, Cloud Run with direct egress, ILBs) in its subnets.
**How:** The network team administers subnets, firewalls, routes and hybrid links in the host project. App teams get `roles/compute.networkUser` on *specific subnets*, so they consume the network without being able to change it. Billing and IAM for workloads stay in each service project.
**GCP:** This is the standard enterprise and bank pattern, usually one host project per environment (prod / non-prod), each with hybrid connectivity to on-prem. It's a separation-of-duties control in its own right.

### Network Connectivity Center (NCC)
`working` · Related: VPC Network Peering, Cloud Interconnect, Hub and spoke
**What:** A hub-and-spoke service that connects VPCs (VPC spokes), on-prem sites (hybrid spokes: VPN, Interconnect, router appliances) and producer services.
**How:** Supports **mesh** (full transitivity between spokes) or **star** (spokes reach the centre but not each other) topologies, with prefix filters per spoke. It solves the transitivity limits of peering, and supports site-to-site data transfer between on-prem locations over Google's backbone.

### Cloud VPN (HA VPN)
`core` · Related: VPN and IPsec, Cloud Router, Cloud Interconnect
**What:** Managed IPsec site-to-site VPN. **HA VPN** has a gateway with two interfaces (two public IPs), and with two tunnels plus BGP it carries a **99.99% SLA**. *Classic VPN* (a single interface, static routing allowed) is legacy.
**How:** Each tunnel tops out at a few Gbps. Add more tunnels for more throughput (ECMP). Routes are dynamic through Cloud Router. It can also connect GCP to AWS or Azure, or two GCP VPCs.
**Watch out:** **HA VPN over Cloud Interconnect** encrypts traffic on a private Interconnect. Some banks require it, because Interconnect isn't encrypted by default (MACsec is the L2 alternative).

### Cloud Interconnect (Dedicated, Partner, Cross-Cloud)
`core` · Related: Cloud VPN, BGP, VLAN attachments
**What:** Private, high-bandwidth, low-latency links between on-prem and Google that bypass the internet. **Dedicated:** your own 10 or 100 Gbps circuits in a Google colocation facility. **Partner:** through a service provider, 50 Mbps–50 Gbps, when you aren't in a Google colo. **Cross-Cloud Interconnect:** dedicated links to AWS, Azure, OCI and others.
**How:** You create **VLAN attachments** on the connection, each attached to a Cloud Router (BGP). Redundancy determines the SLA: **99.9%** needs two connections in one metro (different edge availability domains). **99.99%** needs four connections across two metros and two regions. Traffic isn't encrypted by default; options are **MACsec** (L2) or HA VPN over Interconnect.
**GCP:** UK banks typically use Dedicated Interconnect in London colocation facilities, in a 99.99% topology across two metros, plus encryption.

### Direct Peering and Carrier Peering
`aware` · Related: Cloud Interconnect
**What:** BGP peering with Google's edge to reach Google's *public* services (Workspace, public APIs) at lower cost. **Carrier Peering** goes through a provider. A **Verified Peering Provider** offers internet connectivity to Google with peering already in place. **It doesn't give access to VPC resources.** Interconnect is the option for VPC access.

### Cloud Load Balancing family
`core` · Related: Load balancing (L4 vs L7), Backend services, Cloud Armor, Health checks
**What:** One brand, several products. **Application Load Balancers (L7, Envoy- or GFE-based proxies):** global external, regional external, regional internal, cross-region internal. **Network Load Balancers (L4):** *proxy* NLBs (TCP/SSL proxy, external or internal, global or regional) and *passthrough* NLBs (regional, external or internal; the client IP is preserved; TCP, UDP, ESP, ICMP).
**How:** The building blocks are **forwarding rule** (IP:port) → **target proxy** (holds certificates and SSL policy) → **URL map** (host and path routing; Application LBs only) → **backend service** (balancing mode, affinity, timeouts, Cloud Armor, CDN, IAP) → **backends** (instance groups or NEGs) + **health check**. Passthrough NLBs skip the proxy and URL map.
**GCP:** Picking one: HTTP(S) → Application LB (global external for worldwide users and anycast; regional when traffic must stay in one region for residency; internal for private service-to-service). Non-HTTP → proxy NLB, or passthrough when you need the client IP, UDP, or the highest performance.

### Backend services and NEGs
`working` · Related: Cloud Load Balancing, Cloud Run, Hybrid connectivity
**What:** A **backend service** groups backends and holds the load-balancing settings. **Network Endpoint Groups (NEGs)** are flexible backend types: **zonal NEGs** (IP:port, used for GKE container-native load balancing), **serverless NEGs** (Cloud Run, Cloud Run functions, App Engine, API Gateway), **internet NEGs** (external origins), **hybrid NEGs** (on-prem endpoints over Interconnect or VPN) and **PSC NEGs** (published services or Google APIs).
**GCP:** "Put Cloud Run behind a load balancer" means a serverless NEG. That's how you add Cloud Armor, IAP, a custom domain or multi-region failover to Cloud Run.

### Health checks
`core` · Related: Cloud Load Balancing, Managed Instance Groups, Probes
**What:** Periodic probes (TCP, HTTP(S), HTTP/2, gRPC) that mark backends healthy or unhealthy.
**How:** Load balancer health checks steer traffic away from unhealthy backends. **Autohealing** health checks on a MIG recreate broken VMs. Make them check something meaningful (for example a `/healthz` that verifies the app is ready), but not deep dependencies, or one database blip takes the whole fleet out.
**Watch out:** Allow the probe ranges `35.191.0.0/16` and `130.211.0.0/22` in your firewall.

### Traffic management on Application Load Balancers
`working` · Related: Deployment strategies, URL map
**What:** Advanced L7 features: weighted traffic splitting (canary), request mirroring (shadow traffic), URL and header rewrites, redirects, retries, timeouts, fault injection, and outlier detection (ejecting misbehaving backends).
**GCP:** Configured in the URL map and backend service. It's the same Envoy-based model as a service mesh.

### Cloud CDN and Media CDN
`working` · Related: CDN and edge caching, Cloud Load Balancing
**What:** Edge caching attached to an external Application Load Balancer's backends (buckets, MIGs, Cloud Run, external origins). Supports signed URLs and cookies for private content, cache modes, and invalidation by path. Media CDN is built for large-scale streaming.

### Cloud Armor
`core` · Related: DDoS, WAF, Cloud Load Balancing
**What:** Google's WAF and DDoS protection, enforced at Google's edge on external load balancers (and some internal ones).
**How:** Security policies are attached to backend services. Rules match on IP or CIDR, geography, headers and request attributes (in a CEL-like language) and **preconfigured WAF rules** (based on the OWASP Core Rule Set: SQL injection, cross-site scripting, local and remote file inclusion…). Other features: **rate limiting** (throttle or ban), **Adaptive Protection** (machine-learning detection of L7 DDoS, with suggested rules), **bot management** (reCAPTCHA), **edge security policies** (for CDN or bucket content), threat-intelligence lists, and *preview mode* to test rules before enforcing them.
**Watch out:** Cloud Armor protects things *behind a load balancer*. A VM with a public IP isn't covered.

### Cloud DNS
`core` · Related: DNS, Hybrid DNS, Private Service Connect
**What:** Managed authoritative DNS with a 100% availability SLA. **Public zones** answer the internet. **Private zones** are visible only to the VPCs you authorize.
**How:** It also provides **forwarding zones** (send queries for `corp.bank.co.uk` to on-prem DNS servers), **peering zones** (resolve using another VPC's DNS view, the usual pattern with Shared VPC and hub networks), **inbound server policies** (an IP in your VPC that on-prem servers can forward queries to), **response policies** (override answers), **routing policies** (weighted, geolocation, failover with health checks), **DNSSEC** and **cross-project binding**.
**Watch out:** **Split-horizon** = the same name resolves to different answers inside and outside the network. Very common with private endpoints.

### Hybrid DNS
`working` · Related: Cloud DNS, Cloud Interconnect, Private Google Access
**What:** Making names resolve correctly in both directions between on-prem and GCP.
**How:** Cloud → on-prem: Cloud DNS **forwarding zones** to on-prem resolvers. On-prem → cloud: on-prem servers forward to a Cloud DNS **inbound server policy** IP. For private API access from on-prem, create private zones for `googleapis.com` that map to the `private` or `restricted` VIPs or to PSC endpoints, and advertise those IPs over BGP.
**Watch out:** Hybrid DNS is the most common reason "PSC or PGA works from cloud VMs but not from on-prem".

### Secure Web Proxy
`working` · Related: Forward proxy, Cloud NAT, Egress control
**What:** A managed, cloud-native **explicit forward proxy** for *egress* web traffic from workloads.
**How:** Policies allow or deny by source (secure tags, service accounts, IPs) and by destination host or URL, with optional **TLS inspection** using Certificate Authority Service. It logs every request.
**GCP:** It's the bank answer to "servers may only call these approved external APIs (payment schemes, a market-data vendor)". Cloud NAT alone can't filter by hostname.

### Cloud IDS and Packet Mirroring
`aware` · Related: Cloud NGFW, VPC Flow Logs
**What:** **Packet Mirroring** clones VM traffic to collectors for inspection. **Cloud IDS** is a managed intrusion *detection* service (Palo Alto threat signatures) that uses mirrored traffic and raises alerts but doesn't block. For in-line prevention, use Cloud NGFW Enterprise.

### VPC Flow Logs and Firewall Rules Logging
`working` · Related: Network Intelligence Center, Cloud Logging
**What:** **VPC Flow Logs** sample network flows (5-tuple, bytes, packets, latency) per subnet or VM for troubleshooting, forensics and cost analysis. **Firewall Rules Logging** records which rule allowed or denied a connection.
**Watch out:** Both can generate a lot of log volume and cost. Tune the sampling rate and aggregation interval.

### Network Intelligence Center
`working` · Related: VPC Flow Logs, ICMP and ping
**What:** GCP's network diagnostics suite. **Connectivity Tests** (configuration analysis: "why can't A reach B?", naming the blocking route or firewall rule), **Network Topology** (a visual map with traffic), **Performance Dashboard** (packet loss and latency), **Firewall Insights** (shadowed, unused and overly permissive rules), **Network Analyzer** (detects misconfigurations automatically) and **Flow Analyzer**.

### GKE networking
`working` · Related: Subnet secondary ranges, Kubernetes Services, Gateway API
**What:** How Kubernetes networking maps onto a VPC. **VPC-native clusters** give Pods real VPC IPs from secondary ranges (alias IPs), so Pods are routable and reachable through firewall rules, peering and load balancers.
**How:** Plan three ranges: nodes (primary), Pods (secondary, usually large), Services (secondary). **Private clusters** have nodes with internal IPs only. The control plane is reached through a private endpoint (or a DNS-based endpoint) plus **authorized networks**. **GKE Dataplane V2** (eBPF, based on Cilium) enforces **network policies** and gives visibility. **Container-native load balancing** sends traffic straight to Pod IPs through NEGs. **Gateway API** is the modern way to configure GKE load balancers (it replaces Ingress).
Egress from Pods to non-cluster destinations is **SNAT'd to the node IP** unless the **IP masquerade agent** config excludes the destination ranges (important when on-prem firewalls expect Pod IPs). In-cluster DNS is **kube-dns** (with **NodeLocal DNSCache** for performance) or **Cloud DNS for GKE**. **external-dns** can publish Service and Ingress names into Cloud DNS.
**Watch out:** IP exhaustion of the Pod range is a classic GKE scaling failure. Fixes are additional Pod ranges, smaller max-Pods-per-node, or non-RFC 1918 ranges.

### Network egress costs
`working` · Related: Ingress and egress, CDN, Regions and zones
**What:** Data *into* Google Cloud is free. Data *out* is billed: to the internet (per GB, tiered), between regions, and between zones (a small per-GB charge). Traffic within a zone over internal IPs is free. Interconnect egress is cheaper than internet egress.
**Watch out:** Chatty cross-region designs, streaming data across regions and serving big files without a CDN are hidden cost drivers. A single-region design with a cross-region DR copy usually costs far less than active-active.

### IP address planning (IPAM)
`working` · Related: CIDR and subnetting, GKE networking, Private NAT
**What:** Allocating non-overlapping ranges across on-prem, every VPC and every environment, with room to grow.
**GCP:** Use custom-mode VPCs, reserve large blocks per environment and region, keep GKE Pod ranges separate, use **internal ranges** resources to reserve space, and use Private NAT or PSC where overlaps can't be avoided. Banks usually get ranges from a central network team. Ask early.

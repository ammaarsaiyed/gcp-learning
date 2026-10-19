# 01 · Networking fundamentals

Cloud networking is ordinary networking with software-defined parts. If these ideas are solid, every GCP networking product becomes an obvious variation on something you already understand.

**Tiers:** `core` = you should be able to explain it and design with it · `working` = you should be able to explain it · `aware` = you should know what it is and when it comes up.

---

### OSI and TCP/IP layers
`core` · Related: TCP, Load balancing (L4 vs L7), Firewall
**What:** A model that splits networking into layers, each relying on the one below. The practical version: L2 link (Ethernet, MAC addresses), L3 network (IP addresses, routing), L4 transport (TCP/UDP, ports), L7 application (HTTP, gRPC, DNS). TLS sits between L4 and L7.
**How:** Each layer wraps the one above in its own header (encapsulation). A router only reads L3 headers. An L4 load balancer reads IPs and ports. An L7 load balancer terminates the connection and reads the HTTP request (path, headers, cookies).
**GCP:** The product names tell you the layer. "Application Load Balancer" is L7, "Network Load Balancer" is L4. VPC firewall rules work at L3/L4 (IP, protocol, port). Cloud Armor and Cloud NGFW Enterprise inspect L7.
**Watch out:** When someone says "layer 7", they mean "it understands HTTP". That's what allows path-based routing, WAF rules and header rewrites.

### IP address (IPv4 / IPv6)
`core` · Related: CIDR and subnetting, Private address ranges, NAT
**What:** A numeric address for a network interface. IPv4 is 32 bits, written as four octets (10.1.2.3), about 4.3 billion in total, which ran out long ago. IPv6 is 128 bits (2001:db8::1), effectively unlimited.
**How:** An address has a network part and a host part, split by the prefix length. Routers forward packets based on the network part.
**GCP:** VMs get an internal IP from their subnet and, optionally, an external IP. Both can be ephemeral (released when the resource stops or is deleted) or static (reserved, and billed while unused). Subnets can be dual-stack (IPv4 + IPv6).
**Watch out:** An external IP on a VM is an attack surface. The secure default in banks is no external IPs at all, enforced by org policy.

### CIDR and subnetting
`core` · Related: IP address, VPC subnet, IPAM
**What:** CIDR notation `10.10.0.0/24` means "the first 24 bits are the network, the rest are hosts". The size of a block is 2^(32 − prefix): /24 = 256 addresses, /20 = 4,096, /16 = 65,536, /28 = 16.
**How:** Smaller prefix number = bigger block. Blocks must not overlap within a routed network. Subnetting splits a big block into smaller ones (a /16 holds 256 /24s).
**GCP:** Every subnet has a primary CIDR range and, optionally, secondary ranges (used for GKE Pods and Services). GCP reserves 4 addresses in each primary range (network, gateway, second-to-last, broadcast). You can expand a subnet's range without downtime, but you can't shrink it.
**Watch out:** Overlapping ranges are permanent pain. Peering, VPN and Interconnect all fail or need NAT tricks when on-prem and cloud ranges overlap. That's why banks run central IP address management (IPAM).

### Private address ranges (RFC 1918)
`core` · Related: NAT, Private Google Access, IPAM
**What:** Address ranges reserved for private networks that are never routed on the public internet: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. Also common: `100.64.0.0/10` (carrier-grade NAT space).
**How:** Private hosts reach the internet through NAT, which swaps their private source address for a public one.
**GCP:** VPC subnets normally use RFC 1918 ranges. GCP also supports non-RFC 1918 ranges and *privately used public IPs* (PUPI) when the 10/8 space is exhausted, which happens in large GKE estates.

### Ports
`core` · Related: TCP, UDP, Firewall, Socket and the 5-tuple
**What:** A 16-bit number (0–65535) that identifies which application on a host gets the traffic. The IP finds the machine and the port finds the process.
**How:** Servers listen on well-known ports (0–1023) or registered ports. Clients use a random high *ephemeral* port for their side of the connection (Linux uses 32768–60999 by default). Ports worth knowing by heart: 22 SSH, 53 DNS, 80 HTTP, 443 HTTPS (and HTTP/3 over UDP 443), 25/587 SMTP, 123 NTP, 179 BGP, 389/636 LDAP/LDAPS, 500/4500 IPsec IKE/NAT-T, 1433 SQL Server, 3306 MySQL, 3389 RDP, 5432 PostgreSQL, 6379 Redis, 8080 alternative HTTP (Cloud Run's default `$PORT`), 9092 Kafka, 27017 MongoDB.
**GCP:** Firewall rules allow protocol + port (for example `tcp:443`). Cloud NAT gives each VM a fixed number of source ports per NAT IP, which is why "port exhaustion" is a NAT problem.
**Watch out:** "Open port 22 to 0.0.0.0/0" is a classic finding in Security Command Center. Use IAP TCP forwarding instead.

### Socket and the 5-tuple
`working` · Related: Ports, Firewall, NAT
**What:** A connection is identified by 5 values: source IP, source port, destination IP, destination port and protocol.
**How:** Stateful firewalls, NAT gateways and load balancers all track connections by this 5-tuple. Hash-based load balancing uses it (or part of it) to keep a connection on the same backend.
**GCP:** Passthrough Network Load Balancers distribute by a hash of the 5-tuple (configurable down to 3- or 2-tuple for affinity).

### TCP
`core` · Related: TCP three-way handshake, UDP, Ports
**What:** Transmission Control Protocol: a connection-oriented, reliable, ordered byte stream. It's used by HTTP/1.1, HTTP/2, TLS, databases and SSH.
**How:** Sequence numbers order the bytes. Acknowledgements (ACKs) confirm receipt. Missing data is retransmitted. *Flow control* (the receive window) stops a fast sender overwhelming a slow receiver. *Congestion control* (slow start, then backing off on loss) shares the network fairly.
**Watch out:** Reliability costs latency. One lost packet stalls everything behind it, which is *head-of-line blocking*.

### TCP three-way handshake
`core` · Related: TCP, TLS handshake, Latency and RTT, Keep-alive and connection pooling
**What:** How a TCP connection opens: client sends **SYN** → server replies **SYN-ACK** → client sends **ACK**. Data can flow after that.
**How:** Each side picks an initial sequence number and the other acknowledges it, so both agree on where the byte stream starts. The cost is one full round trip (RTT) before the first byte of the request. Closing uses FIN/ACK in each direction. **RST** aborts a connection immediately ("connection reset").
**GCP:** Load balancer health checks are often just "can I complete a TCP handshake on this port". Global external load balancers complete the handshake at the Google edge near the user, so users don't pay the long RTT to your region.
**Watch out:** A *SYN flood* (a DDoS attack) sends SYNs and never finishes the handshake, filling the server's half-open connection table. Google's edge absorbs this for proxied load balancers.

### UDP
`core` · Related: TCP, QUIC and HTTP/3, DNS
**What:** User Datagram Protocol: no connection, no handshake, no delivery or ordering guarantees. Just send the packet.
**How:** It's lower latency, and it suits cases where late data is useless (voice, video, games) or where the application handles reliability itself (QUIC). DNS queries usually use UDP 53.
**GCP:** Only *passthrough* Network Load Balancers handle general UDP. Proxy load balancers don't.

### Latency, RTT, bandwidth and throughput
`core` · Related: TCP three-way handshake, CDN, Regions and zones
**What:** *Latency* = time for data to arrive. *RTT* = there and back. *Bandwidth* = the pipe's capacity. *Throughput* = what you actually achieve. *Jitter* = variation in latency. *Packet loss* = dropped packets.
**How:** Light in fibre covers about 200 km per millisecond, so 1,000 km adds roughly 10 ms of RTT. London ↔ Belgium is single-digit milliseconds, and London ↔ US East is about 70–80 ms. Every RTT you remove (connection reuse, TLS 1.3, edge termination, caching) cuts user-visible latency. Throughput on a single TCP flow is capped by window size ÷ RTT (the bandwidth-delay product).
**GCP:** Same zone is sub-millisecond, cross-zone is about 1 ms, cross-region is tens of milliseconds. Synchronous replication across regions adds that latency to every write. That's why Cloud SQL HA is synchronous within a region but cross-region replicas are asynchronous.

### MTU and fragmentation
`working` · Related: VPN and IPsec, Cloud Interconnect
**What:** Maximum Transmission Unit: the largest packet a link carries. Ethernet's standard is 1500 bytes, and "jumbo frames" are about 9000.
**How:** A packet bigger than a link's MTU gets fragmented or dropped. Tunnels (IPsec, GRE) add headers, which shrinks the usable payload. *MSS clamping* tells TCP peers to send smaller segments.
**GCP:** VPC MTU defaults to 1460 and can be set between 1300 and 8896. HA VPN has a lower effective MTU because of encryption overhead. Mismatched MTUs cause the classic symptom: "small requests work, big responses hang".

### ICMP, ping and traceroute
`working` · Related: Firewall, Network Intelligence Center
**What:** ICMP carries control messages: echo request/reply (ping), "destination unreachable", "time exceeded" (which traceroute uses).
**GCP:** ICMP must be allowed by firewall rules (the auto-created `default` network allows it, custom VPCs don't). Prefer **Connectivity Tests** in Network Intelligence Center: it analyzes the configuration (routes, firewalls) and tells you *why* a path is blocked, without sending traffic.

### Routing and route tables
`core` · Related: BGP, Default route, VPC routes
**What:** Deciding the next hop for a packet. Each route says "traffic to this CIDR goes to this next hop".
**How:** **Longest prefix match** wins: a /24 route beats a /16 route, which beats the 0.0.0.0/0 default route. Ties are broken by priority or metric.
**GCP:** A VPC has system routes (one per subnet, plus a default internet route), custom static routes, dynamic routes learned through Cloud Router (BGP) and policy-based routes (match on source, protocol and so on). Next hops can be an internet gateway, a VM, an internal passthrough load balancer (for appliance HA), a VPN tunnel or an Interconnect VLAN attachment.

### Default route (0.0.0.0/0)
`working` · Related: Routing, Cloud NAT, Private Google Access
**What:** The "everything else" route, used when nothing more specific matches.
**GCP:** A new VPC has a default route to the *default internet gateway*. A VM still needs an external IP or Cloud NAT to actually reach the internet. Banks often delete this route and send 0.0.0.0/0 to a firewall appliance or to on-prem (forced tunnelling). In that case, Google API traffic needs its own path (Private Google Access with specific routes).

### BGP (Border Gateway Protocol)
`working` · Related: Cloud Router, Cloud Interconnect, Cloud VPN
**What:** The routing protocol that connects separate networks (autonomous systems, each with an ASN) by exchanging which prefixes each can reach.
**How:** Peers open a TCP session (port 179) and advertise routes with attributes. AS-path length and MED influence which path is preferred. **BFD** (Bidirectional Forwarding Detection) detects a dead link in under a second instead of waiting for BGP timers.
**GCP:** **Cloud Router** is Google's managed BGP speaker. It peers with your on-prem routers over HA VPN or Interconnect, advertises your subnets and learns your on-prem prefixes. The VPC's *dynamic routing mode* (regional or global) controls whether routes learned in one region are used by every region.

### NAT (Network Address Translation)
`core` · Related: Cloud NAT, Private address ranges, Ports
**What:** Rewriting addresses as packets cross a boundary. **SNAT** rewrites the source (private VM → public IP going out). **DNAT** rewrites the destination (public IP → private server coming in). **PAT** shares one public IP across many hosts by also rewriting ports.
**How:** The NAT device keeps a translation table keyed by the 5-tuple, so replies find their way back. Outbound-only NAT means unsolicited inbound connections have nowhere to go, which is a security benefit.
**GCP:** **Cloud NAT** is software-defined SNAT for private VMs, GKE nodes and serverless egress. It isn't a box in the traffic path. **Private NAT** translates between VPCs or spokes with overlapping ranges.
**Watch out:** Each NAT IP has about 64k ports. Lots of connections to the *same* destination can exhaust them. The fixes are dynamic port allocation, more NAT IPs and connection reuse.

### Anycast
`working` · Related: Load balancing, CDN, DNS
**What:** The same IP address is advertised from many locations at once, and the internet routes each user to the nearest one.
**GCP:** A global external Application Load Balancer has **one anycast IP** served from Google's edge locations worldwide. Users connect to the nearest edge, then traffic rides Google's private backbone to the healthy backend region. Cloud DNS also serves from anycast name servers.

### DNS
`core` · Related: Cloud DNS, Hybrid DNS, TLS handshake
**What:** The Domain Name System maps names to records (mostly IP addresses). It's distributed, hierarchical and heavily cached.
**How:** Your app asks a *stub resolver* → which asks a *recursive resolver* → which asks a *root server* ("who handles .com?") → the *TLD server* ("who handles example.com?") → the *authoritative server*, which returns the answer. Each answer is cached for its **TTL**. Record types: **A** (IPv4), **AAAA** (IPv6), **CNAME** (alias to another name), **MX** (mail), **TXT** (verification, SPF), **NS** (delegation), **SOA** (zone metadata), **PTR** (reverse lookup), **SRV** (service and port), **CAA** (which CAs may issue certificates). **DNSSEC** signs records so answers can't be forged.
**GCP:** Cloud DNS hosts public and private zones. Every VPC also has an internal resolver at `169.254.169.254` that resolves internal VM names and private zones.
**Watch out:** Changes take up to the TTL to propagate. Lower the TTL *before* a migration cut-over. Many outages are DNS problems.

### HTTP basics
`core` · Related: HTTP versions, REST, HTTP status codes
**What:** The request/response protocol of the web. A request has a method (GET, POST, PUT, PATCH, DELETE), a path, headers and an optional body. A response has a status code, headers and a body.
**How:** HTTP is stateless. Each request carries everything needed (cookies or tokens identify the caller). Important headers: `Host`, `Authorization`, `Content-Type`, `Cache-Control`, `X-Forwarded-For` (original client IP behind a proxy), `traceparent` (tracing).
**GCP:** Load balancers add `X-Forwarded-For` and `Via` headers. Cloud Run, App Engine and Cloud Functions are HTTP-native.

### HTTP/1.1 vs HTTP/2 vs HTTP/3 (QUIC)
`working` · Related: gRPC, TCP, UDP
**What:** **HTTP/1.1** sends one request at a time per connection, so browsers open several connections. **HTTP/2** multiplexes many concurrent streams over one TCP connection, uses binary framing and compresses headers. **HTTP/3** runs over **QUIC** (on UDP), with built-in TLS 1.3, so a lost packet only stalls its own stream and connections survive network changes.
**GCP:** External Application Load Balancers support HTTP/2 and HTTP/3 towards clients. **gRPC needs HTTP/2.** For Cloud Run that means HTTP/2 end-to-end (the `--use-http2` flag) when you need streaming.

### TLS (Transport Layer Security)
`core` · Related: TLS handshake, Certificates and PKI, mTLS
**What:** The protocol that encrypts and authenticates a connection (the "S" in HTTPS). It provides **confidentiality** (encryption), **integrity** (tampering is detected) and **server authentication** (a certificate proves the server's identity). TLS 1.2 and 1.3 are current. SSL and TLS 1.0/1.1 are deprecated.
**How:** Asymmetric cryptography authenticates and agrees on keys. Symmetric cryptography (for example AES-GCM) then encrypts the bulk data, because it's fast.
**GCP:** TLS terminates at Google Front Ends and load balancers using Google-managed or self-managed certificates (through **Certificate Manager**). **SSL policies** set the minimum TLS version and cipher suites. Banks typically require TLS 1.2+ and strong ciphers.

### TLS handshake
`core` · Related: TCP three-way handshake, Certificates and PKI, Latency and RTT
**What:** How a client and server agree on keys and verify identity before sending encrypted data.
**How:** In TLS 1.3, after the TCP handshake: (1) **ClientHello**: the TLS version, supported cipher suites, a key share (ephemeral Diffie-Hellman public value) and **SNI** (the hostname wanted). (2) **ServerHello**: the chosen cipher plus the server's key share, then (encrypted) its **certificate** and a signature proving it owns the certificate's private key, then Finished. (3) Both sides derive the same session keys from the Diffie-Hellman exchange, the client checks the certificate chain against trusted roots, and application data flows. That's **1 RTT** (TLS 1.2 needed 2). Ephemeral keys give **forward secrecy**: stealing the server's private key later can't decrypt past sessions.
**Watch out:** A new HTTPS connection costs TCP (1 RTT) + TLS (1 RTT) before the first byte. Connection reuse and edge termination matter a lot for latency.

### Certificates and PKI
`core` · Related: TLS, mTLS, Certificate Authority Service
**What:** An X.509 **certificate** binds a public key to an identity (a domain name, or a service identity), signed by a **Certificate Authority (CA)**. **PKI** is the system of CAs, trust anchors (root certificates in the trust store) and policies.
**How:** Chain of trust: leaf certificate ← intermediate CA ← root CA (trusted by the client). You generate a key pair, send a **CSR** (certificate signing request) to the CA, and the CA signs it. Certificates expire (public ones now last about a year or less), and they can be revoked (CRL/OCSP).
**GCP:** **Certificate Manager** holds Google-managed public certificates (auto-renewed) or uploaded ones for load balancers. **Certificate Authority Service** runs your *private* CA for internal mTLS and devices.
**Watch out:** Expired certificates are one of the most common causes of outages. Automate renewal.

### mTLS (mutual TLS)
`core` · Related: TLS, Service mesh, Zero trust
**What:** TLS where **both** sides present certificates, so the server also verifies the client's identity.
**How:** During the handshake the server sends a CertificateRequest. The client sends its certificate and proves it holds the private key. The server validates it against a trusted CA. Identity then comes from the certificate rather than from network location.
**GCP:** A **service mesh** (Cloud Service Mesh) gives automatic mTLS between workloads, with certificates issued and rotated for you. External Application Load Balancers can require client certificates (frontend mTLS), as used by Open Banking APIs and B2B partners. Inside Google's infrastructure, services authenticate with ALTS, Google's mTLS-like system.

### SNI (Server Name Indication)
`aware` · Related: TLS handshake
**What:** A field in ClientHello naming the hostname wanted, so one IP can serve many TLS sites with different certificates. Load balancers and Secure Web Proxy use it to pick a certificate or apply policy without decrypting the traffic.

### TLS termination, offload and re-encryption
`working` · Related: Load balancing, Encryption in transit
**What:** *Termination* = the proxy decrypts TLS. *Offload* = the backend receives plain HTTP. *Re-encryption* = the proxy opens a new TLS connection to the backend.
**GCP:** External Application Load Balancers terminate client TLS at the edge. Traffic from the Google Front End to backends is encrypted automatically within Google's network for most backend types, and you can set the backend protocol to HTTPS or HTTP/2 for explicit re-encryption. Banks often require end-to-end TLS as policy, so expect to configure backends for HTTPS.

### Forward proxy vs reverse proxy
`core` · Related: Load balancing, Secure Web Proxy, API gateway
**What:** A **forward proxy** acts for *clients* going out (corporate egress filtering: "which websites may servers reach"). A **reverse proxy** acts for *servers* receiving traffic (load balancers, API gateways, CDNs, WAFs).
**GCP:** Reverse proxies: Application Load Balancers, proxy Network Load Balancers, Apigee, IAP. Forward proxy: **Secure Web Proxy** (managed egress filtering by host or URL, with optional TLS inspection).

### Load balancing (L4 vs L7)
`core` · Related: Cloud Load Balancing, Health checks, Anycast
**What:** Spreading traffic across healthy backends. **L4** balances connections (IP and port) without understanding the content. **L7** understands HTTP, so it can route by host or path, terminate TLS, add headers, cache and apply a WAF.
**How:** Algorithms include round robin, least connections/requests, weighted, and hash-based (for stickiness). **Health checks** remove failed backends. **Session affinity** pins a client to a backend, using a cookie or IP hash. A *proxy* load balancer opens a new connection to the backend (the backend sees the proxy's IP). A *passthrough* load balancer forwards packets unchanged (the backend sees the client's IP).
**GCP:** See *Cloud Load Balancing* in the GCP networking atlas.

### Firewall (stateful vs stateless)
`core` · Related: VPC firewall rules, Cloud NGFW, Network segmentation
**What:** Allows or denies traffic by rules on the 5-tuple (and, for next-generation firewalls, on application content, identity or threat signatures).
**How:** A **stateful** firewall remembers connections: allow the outbound request and the reply is automatically allowed back in. A **stateless** one evaluates every packet on its own, so you need rules in both directions. Rules have a priority, and the first match wins.
**GCP:** VPC firewall rules and Cloud NGFW policies are **stateful**, distributed and enforced at each VM's virtual NIC. They aren't a box traffic flows through, so there's no choke point.

### Ingress and egress
`core` · Related: Firewall, Cloud NAT, VPC Service Controls, Network egress costs
**What:** **Ingress** = traffic coming *in* across a boundary. **Egress** = traffic going *out*. Always ask "relative to what boundary?" (a VM, a VPC, a perimeter, Google's network).
**How:** The word appears in several GCP contexts with different meanings: (1) **Firewall rules** have a *direction*: an ingress rule filters inbound packets, an egress rule outbound. (2) **Billing:** network *ingress is free*, *egress* (to the internet, across regions or zones) is charged. (3) **Cloud Run "ingress" setting:** who may reach the service (all, internal, internal + Cloud Load Balancing). **Cloud Run egress:** whether outbound traffic goes through your VPC. (4) **Kubernetes Ingress:** an API object that configures an L7 load balancer for a cluster (now largely replaced by the Gateway API). (5) **VPC Service Controls ingress/egress rules:** exceptions that allow specific *API calls* to cross a service perimeter.
**Watch out:** In bank security reviews, "egress control" usually means: "can a compromised workload send data to the internet or to an unapproved Google project?" The answer combines no external IPs, Cloud NAT allow-lists or Secure Web Proxy, firewall egress deny rules, and VPC-SC.

### North-south vs east-west traffic
`working` · Related: Ingress and egress, Service mesh, Network segmentation
**What:** **North-south** = traffic in and out of your environment (users ↔ apps, apps ↔ internet). **East-west** = traffic between services inside it.
**How:** Traditional security focused on north-south (the perimeter). Attackers who get in move east-west ("lateral movement"), which is why zero trust and microsegmentation control east-west traffic too.
**GCP:** North-south: load balancers, Cloud Armor, Cloud NAT, Secure Web Proxy. East-west: VPC firewall rules and policies with secure tags or service accounts, service mesh mTLS and authorization policies, GKE network policies.

### Network perimeter, DMZ and trust zones
`core` · Related: Zero trust, VPC Service Controls, Network segmentation
**What:** A **perimeter** is a boundary between zones of different trust, with controls on what crosses it. The classic model is "castle and moat": a hardened edge, with a **DMZ** (a semi-trusted zone for internet-facing servers) between the internet and the trusted internal network.
**How:** Perimeter controls inspect and restrict traffic at the boundary. The weakness: once inside, everything is trusted, and cloud services reached over public APIs bypass the network edge altogether.
**GCP:** GCP has several kinds of perimeter: (1) the **network edge**: load balancers with Cloud Armor, firewall policies, no external IPs; (2) **VPC Service Controls service perimeters**: a boundary around *Google API access to data* (BigQuery, GCS, the AI platform) that blocks data leaving to projects outside the perimeter, even with valid credentials; (3) **identity-based perimeters**: IAP with context-aware access (zero trust). In a bank, "the perimeter" in a design review almost always means VPC-SC plus private networking.

### Network segmentation and microsegmentation
`working` · Related: Firewall, Shared VPC, Secure Tags
**What:** Splitting a network into zones so a breach in one doesn't reach the others. **Microsegmentation** goes down to individual workloads.
**GCP:** You can segment with separate VPCs or projects, subnets per tier, and firewall policies that target **secure tags** or service accounts (which follow the workload, not its IP). GKE network policies segment Pods.

### VPN and IPsec
`working` · Related: Cloud VPN, MTU, BGP
**What:** A VPN creates an encrypted tunnel over an untrusted network. **IPsec** is the standard suite for site-to-site VPNs: **IKE** (UDP 500/4500) negotiates keys, then **ESP** encrypts the packets.
**How:** *Site-to-site* links two networks (data centre ↔ VPC). *Client VPN* links a single user's device. Policy-based VPNs match specific traffic selectors. Route-based VPNs use routes, often learned through BGP.
**GCP:** **HA VPN** is site-to-site IPsec with BGP through Cloud Router, with a 99.99% SLA in the right topology. GCP has no managed client VPN. For users, the model is IAP / zero trust.

### Layer 2 vs Layer 3 connectivity and VLANs
`aware` · Related: Cloud Interconnect
**What:** A **VLAN** splits one physical link into multiple isolated logical networks (802.1Q tags). An L2 connection carries Ethernet frames, and you run your own routing (BGP) over it. An L3 connection is already routed by the provider.
**GCP:** Interconnect uses **VLAN attachments**. Partner Interconnect comes in L2 (you configure BGP with Cloud Router) or L3 (the partner does the BGP) flavours.

### CDN and edge caching
`working` · Related: Cloud CDN, HTTP basics, Anycast
**What:** A Content Delivery Network caches responses at points of presence (PoPs) near users, cutting latency and offloading the origin.
**How:** The cache key is usually host + path + query string. `Cache-Control` headers set the TTL. **Invalidation** removes stale content early. Caches can also serve stale content if the origin fails.
**GCP:** **Cloud CDN** is enabled on an external Application Load Balancer backend (MIGs, buckets, Cloud Run, external origins). **Media CDN** handles large-scale video.
**Watch out:** Never cache personalized or authenticated responses unintentionally. In a bank, that's a data leak.

### DDoS (distributed denial of service)
`working` · Related: Cloud Armor, Anycast
**What:** Overwhelming a service with traffic. **Volumetric / L3–L4** attacks (SYN floods, UDP floods) exhaust bandwidth or connection tables. **L7** attacks send valid-looking HTTP requests that exhaust app resources.
**GCP:** Proxy-based load balancers absorb L3/L4 floods at Google's edge by design. **Cloud Armor** adds L7 defence: rate limiting, WAF rules, bot management and **Adaptive Protection** (machine-learning detection of anomalous traffic).

### Keep-alive and connection pooling
`working` · Related: TCP three-way handshake, TLS handshake, Cloud SQL
**What:** Reusing open connections instead of paying the TCP + TLS setup for every request.
**How:** HTTP keep-alive and HTTP/2 multiplexing reuse client connections. Database **connection pools** keep a set of open DB connections that requests borrow and return.
**GCP:** Cloud SQL has a maximum connection count per instance size. Hundreds of autoscaled Cloud Run instances, each opening its own pool, can exhaust it. Cap `max-instances`, size pools small, or use a pooler (AlloyDB and Cloud SQL offer managed connection pooling for PostgreSQL).

### IPv6
`aware` · Related: IP address
**What:** 128-bit addressing with no shortage and no NAT needed, though usually still protected by firewalls.
**GCP:** Dual-stack subnets, IPv6 on external load balancers (an IPv6 frontend can serve IPv4 backends) and IPv6-only subnets for some workloads. Uncommon in bank internal networks today, but appears in IPAM planning.

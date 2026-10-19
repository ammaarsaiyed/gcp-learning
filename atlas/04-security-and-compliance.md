# 04 · Security, cryptography and compliance

Identity was file 03. This file covers everything else that keeps data safe and auditors satisfied: cryptography, keys, perimeters, guardrails, detection, and compliance tooling.

---

### CIA triad
`core` · Related: Defense in depth, Threat modeling
**What:** The three security goals. **Confidentiality** (only authorized parties see data), **Integrity** (data isn't altered undetected), **Availability** (systems and data are usable when needed).
**How:** Every control serves at least one of them. Encryption and IAM serve confidentiality. Hashing, signatures and audit logs serve integrity. Redundancy and DDoS protection serve availability. Operational resilience regulation is largely about availability.

### Shared responsibility model
`core` · Related: Compliance certifications, Outsourcing (PRA SS2/21)
**What:** Security duties are split between the cloud provider and the customer, and the split moves with the service model.
**How:** Google always secures the physical infrastructure, hardware, hypervisor and global network. For **IaaS** (Compute Engine) you own the OS, patching, apps, data, IAM and network configuration. For **PaaS / serverless** (Cloud Run, BigQuery) Google also handles the OS and runtime, and you own the code, data, IAM and configuration. For **SaaS**, mostly data and access. Google describes this as "shared fate": providing secure defaults, blueprints and guidance as well.
**Watch out:** **Your data, identities and configuration are always your responsibility.** Most cloud breaches are customer misconfigurations: public buckets, over-broad IAM, leaked keys.

### Defense in depth
`core` · Related: Zero trust, VPC Service Controls, Organization Policy
**What:** Layered, independent controls, so one failure doesn't mean a breach.
**GCP:** A typical stack: org policies (guardrails) → IAM least privilege + PAM (identity) → private networking + firewall policies + VPC-SC (network and data perimeter) → CMEK + Sensitive Data Protection (data) → Binary Authorization + vulnerability scanning (supply chain) → Cloud Armor (edge) → audit logs + Security Command Center (detection) → incident response.

### Threat modeling
`working` · Related: Defense in depth, OWASP Top 10 for LLM apps
**What:** Systematically asking "what can go wrong?" for a design. A common framework is **STRIDE**: **S**poofing (identity), **T**ampering (integrity), **R**epudiation (deniability → logs), **I**nformation disclosure, **D**enial of service, **E**levation of privilege.
**How:** Draw the data-flow diagram, mark the **trust boundaries** (where data crosses between zones, services or organizations), list threats at each crossing, and map each one to a control.
**GCP:** Bank architecture boards expect this. Trust boundaries in GCP designs: internet → load balancer, VPC → Google APIs (VPC-SC), project → project, your org → a third-party SaaS or model provider, user prompt → LLM → tools.

### Symmetric vs asymmetric cryptography
`core` · Related: TLS handshake, Envelope encryption, Digital signatures
**What:** **Symmetric:** the same secret key encrypts and decrypts (for example AES-256-GCM). It's fast and used for bulk data. **Asymmetric:** a key pair (public and private; RSA, ECC/ECDSA, Ed25519). Data encrypted with the public key can only be decrypted with the private key, and signatures made with the private key are verified with the public key. It's slow, and used for key exchange, signatures and identity.
**How:** Real systems combine the two. Asymmetric crypto authenticates and agrees on a symmetric session key (TLS), or wraps a symmetric key (envelope encryption).
**GCP:** Cloud KMS supports symmetric keys (encrypt/decrypt), asymmetric signing keys, asymmetric decryption keys and MAC keys. Post-quantum signature algorithms are appearing too.

### Hashing, HMAC and digital signatures
`core` · Related: Symmetric vs asymmetric cryptography, JWT, Webhooks
**What:** A **hash** (for example SHA-256) is a one-way, fixed-size fingerprint: any change to the input changes the hash. An **HMAC** is a hash keyed with a shared secret, proving integrity *and* that the sender knows the secret. A **digital signature** is a hash signed with a private key, proving integrity *and* origin, verifiable by anyone with the public key, and the signer can't deny it later.
**GCP:** Object checksums (CRC32C / MD5) in Cloud Storage, HMAC-signed webhooks, signed URLs (signatures), Binary Authorization attestations (signatures), JWTs (signatures).
**Watch out:** Store passwords with slow, salted hashes (bcrypt, scrypt, Argon2), never with plain SHA-256.

### Encryption at rest (default)
`core` · Related: Envelope encryption, CMEK, Cloud KMS
**What:** All customer data stored in Google Cloud is encrypted at rest by default with AES-256, with no configuration, using Google-managed keys.
**How:** Data is split into chunks, each encrypted with a **data encryption key (DEK)**. DEKs are wrapped by **key encryption keys (KEKs)** held in Google's internal key management service, which is itself protected by a root key in hardware.
**Watch out:** "Is it encrypted at rest?" always has the answer yes. The real bank question is "**who controls the key**, and can we revoke access?". That's CMEK, Cloud HSM and EKM.

### Envelope encryption
`core` · Related: Cloud KMS, CMEK
**What:** Encrypting data with a DEK, then encrypting (wrapping) the DEK with a KEK held in a key management service.
**How:** The encrypted data and the wrapped DEK are stored together. To read, you ask KMS to unwrap the DEK (an authorized, audited call), then decrypt locally. You get speed (bulk crypto happens locally), central control (the KEK never leaves KMS), and cheap rotation (re-wrap the DEKs, not the data).
**GCP:** It's how CMEK works across services. You can do it yourself in apps with KMS and Tink.

### Encryption in transit
`core` · Related: TLS, mTLS, Cloud Interconnect
**What:** Protecting data as it moves.
**GCP:** User → Google: TLS to Google Front Ends. Between Google services: ALTS (mutual authentication + encryption). VM ↔ VM traffic inside Google's network: encrypted at the network layer when it leaves physical boundaries Google controls, plus your own TLS or mTLS if policy requires it. Hybrid: HA VPN (IPsec), MACsec on Interconnect, or application TLS.
**Watch out:** Banks typically mandate TLS 1.2+ end to end, including load balancer → backend. Plan backend certificates or a service mesh.

### Confidential Computing (encryption in use)
`working` · Related: Encryption at rest, CIA triad
**What:** Keeps data encrypted **in memory while being processed**, using hardware-based trusted execution environments (AMD SEV / SEV-SNP, Intel TDX, NVIDIA confidential GPUs), with remote **attestation** proving the environment's integrity.
**GCP:** Confidential VMs, Confidential GKE Nodes, Confidential Dataproc and **Confidential Space** (multi-party computation, where parties combine sensitive data without seeing each other's raw data, for example cross-bank fraud analytics).

### Cloud KMS
`core` · Related: Envelope encryption, CMEK, Cloud HSM, Cloud EKM
**What:** Managed key management: create, rotate, disable and destroy cryptographic keys, and use them through API calls that are fully audited.
**How:** Hierarchy: **key ring** (a location-bound grouping) → **key** (with a purpose and rotation schedule) → **key versions** (the actual key material, one of which is primary). **Protection levels:** SOFTWARE, **HSM** (Cloud HSM, FIPS 140-2 Level 3 validated), **EXTERNAL** / EXTERNAL_VPC (Cloud EKM). Destroying a key version has a scheduled waiting period. IAM separates *admins* (`cloudkms.admin`: manage keys, can't use them) from *users* (`cloudkms.cryptoKeyEncrypterDecrypter`). **Autokey** automates CMEK key creation per resource. **Key import** lets you bring key material generated in your own HSM (wrapped for import), when policy requires keys to originate outside Google.
**Watch out:** Key rings and keys **can't be deleted** (only key versions can be destroyed), and the key's location must match the resource's location for CMEK.

### CMEK (customer-managed encryption keys)
`core` · Related: Cloud KMS, Envelope encryption, Crypto-shredding
**What:** Services (BigQuery, Cloud Storage, Cloud SQL, AlloyDB, Spanner, Pub/Sub, GKE disks, the AI platform's resources, and many more) use **your Cloud KMS key** as the KEK for your data, instead of a Google-internal key.
**How:** You grant the *service agent* of each service `cryptoKeyEncrypterDecrypter` on your key. You control rotation, and **disabling or destroying the key makes the data unreadable**. All key use appears in audit logs. The org policy `gcp.restrictNonCmekServices` can force CMEK on chosen services.
**Watch out:** If you lose or destroy the key, the data is gone for good. Plan key lifecycle and break-glass access carefully.

### CSEK (customer-supplied encryption keys)
`aware` · Related: CMEK
**What:** You supply raw key material with each API call (Cloud Storage and Compute Engine disks only). Google doesn't store the key. It's rarely used now: operationally painful, with CMEK/EKM preferred.

### Cloud HSM
`working` · Related: Cloud KMS, Cloud EKM
**What:** Hardware security modules managed by Google, behind the Cloud KMS API (protection level HSM). Keys never leave the HSM in plaintext. FIPS 140-2 Level 3 validated. It's commonly required for payment and regulated workloads.

### Cloud EKM and Key Access Justifications
`working` · Related: Cloud KMS, Data sovereignty, Access Approval
**What:** **Cloud External Key Manager** uses keys that stay in a **third-party key manager outside Google** (Thales, Fortanix, Entrust and others), reached over the internet or a VPC. **Key Access Justifications (KAJ)** attach a reason code to every key-unwrap request, so your external key manager can approve or deny by policy (for example "deny any request with justification 'Google-initiated access'").
**GCP:** The strongest sovereignty posture: Google can't decrypt without your external system saying yes. The cost is extra latency and an availability dependency on the key manager.

### Key rotation and crypto-shredding
`working` · Related: Cloud KMS, Right to erasure
**What:** **Rotation:** periodically creating a new primary key version, so new data uses new keys and the impact of any compromise is limited. Old versions stay available to decrypt old data. **Crypto-shredding:** destroying a key so all data encrypted under it becomes permanently unreadable, which is a way to "delete" data from backups and logs you can't otherwise purge.
**GCP:** KMS supports automatic rotation schedules for symmetric keys. Some services re-encrypt with the new version only on rewrite.

### Secret Manager
`core` · Related: Cloud KMS, Cloud Run, Service accounts
**What:** Managed storage for API keys, passwords, certificates and connection strings, as versioned **secrets** with per-secret IAM.
**How:** Each secret has versions (enable, disable, destroy). **Replication policy** is *automatic* (Google chooses) or *user-managed* (you pin regions, which matters for residency). There are also regional secrets, CMEK support, rotation *notifications* through Pub/Sub (you implement the rotation logic), expiry, and audit logs of every access. Cloud Run and GKE mount secrets as env vars or files. Workloads read them with `secretmanager.secretAccessor`.
**Watch out:** Pin versions in production deployments. Never bake secrets into images, env files committed to git, or Terraform state in plaintext.

### Certificate Authority Service
`aware` · Related: Certificates and PKI, mTLS, Secure Web Proxy
**What:** A managed private CA (with HSM-backed CA keys) for issuing internal certificates at scale: service mesh, mTLS, devices, Secure Web Proxy TLS inspection.

### VPC Service Controls (service perimeters)
`core` · Related: Network perimeter, Access Context Manager, Private Google Access, Data exfiltration
**What:** A **service perimeter** around a set of projects that controls access to **Google-managed APIs** (BigQuery, Cloud Storage, the AI platform, Spanner, Secret Manager, …). Requests that cross the perimeter are blocked, **even if IAM would allow them**. It's the main data-exfiltration control on GCP.
**How:** You list the **protected projects** and **restricted services**. Inside the perimeter, resources talk freely. A call from outside to a protected API is denied unless it matches an **access level** (IP, device) or an **ingress rule**. A call from inside to a resource *outside* (for example copying a BigQuery table into a personal project) is denied unless an **egress rule** allows it. Ingress and egress rules specify identities, source and destination projects, services and even methods. **Perimeter bridges** link perimeters. **Dry-run mode** logs violations without blocking. For VMs and on-prem traffic, route API calls to `restricted.googleapis.com` so only VPC-SC-supported APIs are reachable.
**GCP:** It's the answer to: "a data scientist with valid credentials copies customer data to a bucket in their own project", "a stolen token is used from the internet", "a compromised VM sends data to an attacker's project".
**Watch out:** It doesn't filter ordinary internet traffic (that's firewalls and Secure Web Proxy), and it doesn't replace IAM. Rollout breaks things in surprising ways (Cloud Build, Logging sinks, cross-project pipelines), so always start in dry-run.

### Organization Policy Service
`core` · Related: IAM vs Org Policy, Resource hierarchy, Data residency
**What:** Centralized **constraints** on what configurations are allowed, inherited down the hierarchy, whatever IAM says.
**How:** Constraints are **boolean** (enforce on or off) or **list** (allow or deny values). Policies can inherit, merge or replace the parent's. **Custom constraints** use CEL on resource fields. **Dry-run** shows impact before enforcing. **Custom organization policies** constrain any supported resource field with CEL (for example "GKE clusters must enable Binary Authorization"). Bank staples: `gcp.resourceLocations` (for example `in:europe-west2-locations`), `iam.allowedPolicyMemberDomains` (domain-restricted sharing), `iam.disableServiceAccountKeyCreation`, `compute.vmExternalIpAccess`, `compute.requireOsLogin`, `storage.publicAccessPrevention`, `storage.uniformBucketLevelAccess`, `sql.restrictPublicIp`, `gcp.restrictNonCmekServices`, `compute.restrictVpcPeering`, `run.allowedIngress`.
**Watch out:** Org policies apply to *new* configuration changes. They don't automatically fix existing violations, so pair them with Security Command Center findings.

### Security Command Center (SCC)
`core` · Related: Cloud Audit Logs, Cloud Asset Inventory
**What:** GCP's security and risk platform: asset inventory, **misconfiguration findings** (Security Health Analytics: public buckets, open firewall rules, keys in use, MFA gaps…), **threat detection** (Event Threat Detection on logs, Container Threat Detection, VM Threat Detection), Web Security Scanner, **posture management** (deploy and check policy sets against benchmarks such as CIS), attack path simulation, AI protection, and compliance reporting. It comes in Standard, Premium and Enterprise tiers.
**GCP:** Banks enable it at the org level and route findings to the SOC's SIEM (often Google Security Operations or Splunk) through Pub/Sub.

### Cloud Audit Logs
`core` · Related: Cloud Logging, Log sinks, Non-repudiation
**What:** Immutable records of "who did what, where, when". **Admin Activity** (configuration changes; always on, free, kept 400 days), **Data Access** (reading data or metadata, and writing data; **off by default except for BigQuery**, can be high volume and costs money), **System Event** (Google-initiated changes such as live migration; always on), **Policy Denied** (VPC-SC and other policy violations).
**How:** Each entry records the principal (`protoPayload.authenticationInfo.principalEmail`, including the impersonation chain), the method, the resource, the caller IP and user agent, and the status. They're stored in the `_Required` (locked) and `_Default` log buckets.
**GCP:** Banks enable Data Access logs for sensitive services (BigQuery, Cloud Storage, KMS, Secret Manager, the AI platform), route them through **aggregated sinks** to a central, locked logging project, and keep them for the retention their regulator requires.

### Log sinks, aggregated sinks and SIEM integration
`working` · Related: Cloud Audit Logs, Cloud Logging, Security Command Center
**What:** A **sink** routes matching logs to a destination: a log bucket, BigQuery, Cloud Storage, Pub/Sub, or another project. **Aggregated sinks** at the org or folder level capture logs from every child project.
**GCP:** The pattern is an org-level aggregated sink → a central logging project (with a bucket lock or locked retention, and restricted access) + Pub/Sub → SIEM. **Google Security Operations** (formerly Chronicle) is Google's SIEM/SOAR.

### Access Transparency and Access Approval
`working` · Related: Cloud Audit Logs, Cloud EKM, Outsourcing (PRA SS2/21)
**What:** **Access Transparency** gives near-real-time logs of actions *Google personnel* take on your content (for example a support engineer accessing data during a case), with a justification. **Access Approval** requires **your explicit approval** before Google personnel can access your content for supported services.
**GCP:** Both answer the outsourcing-risk question "how do we know and control when the provider accesses our data?". They typically need a qualifying support or Assured Workloads tier.

### Assured Workloads
`working` · Related: Data residency, Organization Policy, Access Approval
**What:** A way to create folders pre-configured for a compliance regime. It applies org policies (allowed locations, allowed services), personnel and support controls (for example access only by staff in certain locations), key management requirements and monitoring for drift.
**GCP:** Regimes include US (FedRAMP, IL), EU (EU Data Boundary, sovereign controls) and others. Check what's currently offered for UK requirements. Many UK banks build equivalent controls themselves with org policies, CMEK/EKM and Access Approval.

### Data residency vs data sovereignty
`core` · Related: Organization Policy, Cloud EKM, UK GDPR
**What:** **Residency:** *where* data is physically stored and processed (for example only in UK regions). **Sovereignty:** *whose laws and control* the data is subject to, which covers residency **plus** who can access it (provider staff, foreign legal orders) and who controls the keys.
**How:** Residency tools: `gcp.resourceLocations` org policy, regional resources, user-managed replication for secrets, and regional AI endpoints with a matching ML processing location. Sovereignty tools add: CMEK/EKM with Key Access Justifications, Access Approval, Assured Workloads, and partner-operated sovereign clouds.
**Watch out:** Some services are *global* (IAM, parts of Cloud Logging metadata, some AI model endpoints). Check each service's data-location docs, because "the region is London" doesn't automatically mean every byte stays in London.

### Sensitive Data Protection (Cloud DLP)
`core` · Related: Tokenisation and pseudonymisation, UK GDPR, Model Armor
**What:** Discovers, classifies and de-identifies sensitive data: PII, financial data (card numbers, IBANs, sort codes), credentials and so on.
**How:** **Inspection** uses 150+ built-in **infoTypes** plus custom ones (regex, dictionaries) with likelihood scores. **De-identification** offers masking, redaction, bucketing, date shifting, **tokenisation / pseudonymisation** (deterministic encryption, **format-preserving encryption**, cryptographic hashing), with re-identification possible when the key is held. **Discovery** continuously profiles BigQuery, Cloud Storage and Cloud SQL and tags sensitivity levels.
**GCP:** Typical bank and AI use: redact PII from prompts and logs before they reach an LLM or analytics, tokenize customer IDs in the data lake, and find "shadow" PII in buckets.

### Tokenisation and pseudonymisation
`working` · Related: Sensitive Data Protection, PCI DSS, UK GDPR
**What:** Replacing a sensitive value with a non-sensitive substitute (a token). The mapping is held securely (vault-based) or derived cryptographically (vaultless, for example FPE). Pseudonymised data is still personal data under UK GDPR if it can be re-identified, but its risk is reduced.
**Why it matters:** It shrinks **PCI DSS scope** (systems that only see tokens hold no cardholder data) and allows analytics and ML on de-risked data.

### Shielded VMs
`aware` · Related: Compute Engine, Confidential Computing
**What:** VMs with verified boot integrity: **Secure Boot** (only signed bootloaders and kernels), a **vTPM** and **integrity monitoring** (alerts if the boot measurements change). On by default for most images.

### Binary Authorization
`working` · Related: Software supply chain security, Cloud Build, GKE, Cloud Run
**What:** A deploy-time policy check that only allows **trusted container images** to run on GKE or Cloud Run, for example images built by your Cloud Build pipeline, scanned with no critical CVEs and signed (**attested**) by approvers.
**How:** Policies require attestations (signatures by attestors using KMS keys) or check build provenance. It supports dry-run and break-glass.

### Software supply chain security (SLSA, SBOM, Artifact Analysis)
`working` · Related: Binary Authorization, CI/CD, Artifact Registry
**What:** Securing everything between source code and running software. **SLSA** (Supply-chain Levels for Software Artifacts) is a framework of levels for build integrity and **provenance** (a signed record of how and where an artifact was built). An **SBOM** (Software Bill of Materials) lists every component and dependency.
**GCP:** Cloud Build generates SLSA provenance. **Artifact Analysis** scans images in Artifact Registry for OS and language-package CVEs (on push and continuously). Binary Authorization enforces provenance and attestations. **Assured Open Source Software** provides Google-vetted packages.

### Vulnerability management
`working` · Related: Software supply chain security, Security Command Center
**What:** Finding, prioritizing and fixing weaknesses (CVEs, scored by CVSS) in OS packages, libraries and images, within defined SLAs.
**GCP:** Artifact Analysis (images), VM Manager (OS patch compliance and patch jobs), GKE auto-upgrades and release channels, SCC findings, Web Security Scanner (web app vulnerabilities like XSS).

### Incident response
`working` · Related: Cloud Audit Logs, Security Command Center, Break-glass access
**What:** The process of detecting, containing, eradicating and recovering from security incidents, then learning from them.
**GCP:** Contain by revoking access (disable a service account, remove IAM bindings, disable or rotate keys), isolate VMs (firewall tags), and snapshot disks for forensics. Investigate with audit logs and Log Analytics. Run tested playbooks. Banks also have regulatory notification duties (for example to the ICO within 72 hours for personal data breaches, plus PRA/FCA notifications for material incidents).

### Compliance certifications and attestations
`working` · Related: Shared responsibility model, PCI DSS
**What:** Independent audits showing the provider's controls: **ISO 27001** (information security management), 27017 (cloud security), 27018 (cloud privacy), **SOC 1/2/3** (controls reports), **PCI DSS** (card data), plus regional and sector schemes.
**GCP:** The **Compliance Reports Manager** gives you Google's reports. They cover *Google's* side of the shared responsibility model. You still have to evidence your own controls for your workloads.

### Penetration testing on GCP
`aware` · Related: Incident response, CBEST
**What:** You may pen-test *your own* GCP resources without notifying Google, within the Acceptable Use Policy and Terms of Service (no attacks on Google's infrastructure or other customers, no DoS testing).

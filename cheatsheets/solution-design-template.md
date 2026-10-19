# Solution Design Template

Use this to **design** a solution (fill it in top to bottom) or to **break down** an existing one (label each box in the diagram with a section number, then look for the empty sections; those are the gaps).

---

## 0. Requirements (ask these before drawing anything)

- [ ] **What** does it do? (the 3 core user journeys)
- [ ] **Who** uses it: employees, customers, machines? **How many**, and **where** (one country, global)?
- [ ] **Traffic shape:** steady, spiky, batch, real-time?
- [ ] **Availability (SLO)** and **RTO / RPO**
- [ ] **Latency** target
- [ ] **Data:** volume, growth, sensitivity (PII, PCI, PHI), **residency**
- [ ] **Constraints:** budget, deadline, team skills, existing systems, on-prem dependencies, compliance

## 1. Identity and access
- Human users authenticate with: ______ (Cloud Identity / IAP / Identity Platform)
- Each workload's service account and its *minimal* roles: ______
- External systems authenticate with: ______ (Workload Identity Federation)
- Where in the hierarchy access is granted (folder / project / resource): ______

## 2. Network
- Entry point: ______ (which load balancer, DNS, CDN, Armor)
- VPC layout: ______ (Shared VPC? subnets per region, private IPs)
- Egress: ______ (Cloud NAT, Private Google Access, PSC)
- Hybrid: ______ (VPN / Interconnect)

## 3. Compute
- Service(s) and why (with reference to the compute decision tree): ______
- Scaling model (min/max, scale to zero?): ______
- Zonal / regional / multi-region: ______

## 4. Data
- System of record: ______ (why this database over its neighbors)
- Files/objects: ______ (bucket location, storage class, lifecycle)
- Analytics: ______
- Cache: ______
- Backups, replication, retention: ______

## 5. Integration
- Async flows: ______ (Pub/Sub topics, subscriptions, dead-letter topics)
- Events/schedules/orchestration: ______ (Eventarc, Scheduler, Tasks, Workflows)
- External APIs: ______

## 6. Operations
- CI/CD: ______ (Cloud Build → Artifact Registry → Cloud Deploy / GitHub Actions + WIF)
- IaC: ______ (Terraform)
- Observability: SLIs/SLOs ______, alerts ______, dashboards ______, log sinks ______
- Runbooks / on-call: ______

## 7. Security (beyond IAM)
- Guardrails: ______ (Org Policies)
- Secrets: ______ (Secret Manager)
- Encryption: default / CMEK ______
- Perimeter: ______ (VPC-SC, private IPs only)
- Edge: ______ (Cloud Armor)
- Audit and detect: ______ (Audit Logs, SCC)

## 8. Cost
- Main cost drivers: ______
- Levers: scale to zero, committed use, Spot, storage lifecycle, BigQuery partitioning, CDN for egress
- Budgets, alerts and labels: ______

## 9. Reliability check
- What happens if **a zone** fails? ______
- What happens if **a region** fails? ______
- What happens if **a dependency** is slow or down? ______ (timeouts, retries, queues, circuit breaking)

## 10. Trade-offs (the important part)
| Decision | Because | Given up |
|---|---|---|
| | | |
| | | |

## 11. Diagram
Boxes = services (with lens number), arrows = data flow labeled with *protocol* and *identity* (which service account calls what).

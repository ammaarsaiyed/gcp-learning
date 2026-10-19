# 06 · Storage, databases and data theory

Choosing where state lives is the decision that's hardest to undo. Learn the theory first (consistency, replication, partitioning), and the GCP products then read as different trade-offs between the same properties.

---

### Block vs file vs object storage
`core` · Related: Persistent Disk, Filestore, Cloud Storage
**What:** **Block:** raw volumes the OS formats and mounts (one VM, low latency, used for databases and boot disks): Persistent Disk and Hyperdisk. **File:** a shared hierarchical filesystem over NFS or SMB (many clients, POSIX semantics): Filestore, NetApp Volumes. **Object:** whole immutable objects in a flat namespace, accessed over HTTP APIs, with practically unlimited scale and cheap storage: Cloud Storage.
**Watch out:** Object storage isn't a filesystem. There's no in-place append or edit, and rename is copy + delete. FUSE adapters hide this, but the performance doesn't change.

### Cloud Storage (GCS)
`core` · Related: Storage classes, Signed URLs, Object lifecycle management
**What:** Object storage with very high durability (designed for 11 nines). **Buckets** (globally unique names, with a location and default class) hold **objects** (immutable blobs with metadata).
**How:** **Strong global consistency** for reads after writes, overwrites, deletes and listings. **Locations:** regional, dual-region (with optional turbo replication, an RPO of 15 minutes), multi-region. Access: **uniform bucket-level access** (IAM only, recommended) or legacy ACLs, **public access prevention**, signed URLs. Protection: **object versioning**, **soft delete** (deleted objects recoverable for a set number of days), **retention policies** and **bucket lock** (WORM; it satisfies some record-keeping rules), object holds. Movement: Storage Transfer Service, `gcloud storage`, parallel composite uploads. Data lake integrations through BigLake.
**GCP:** The landing zone for data lakes, model artifacts, RAG source documents, backups, logs archives and static sites.

### Storage classes
`core` · Related: Cloud Storage, Object lifecycle management, Cost
**What:** **Standard** (hot, no minimum), **Nearline** (30-day minimum, about monthly access), **Coldline** (90-day minimum), **Archive** (365-day minimum). All have **millisecond first-byte latency** and the same API and durability. Colder classes cost less to store but more to retrieve, and have early-deletion charges.
**How:** **Autoclass** moves objects between classes automatically based on access. A bucket's class is a default. Each object has its own class.

### Object lifecycle management
`working` · Related: Storage classes, Data retention
**What:** Bucket rules that **change storage class or delete objects** based on conditions: age, created-before date, number of newer versions, live or noncurrent state, prefix or suffix.
**GCP:** For example: move logs to Coldline after 30 days, delete after 7 years. Delete noncurrent versions after 90 days. Lifecycle can't delete objects under a retention policy before it expires.

### Signed URLs and signed policy documents
`working` · Related: Cloud Storage, Service accounts
**What:** Time-limited URLs that grant whoever holds them access to one object (GET to download, PUT to upload) without an IAM identity. Signed with a service account key or, keylessly, through the IAM `signBlob` API.
**GCP:** The standard pattern for browser and mobile uploads straight to Cloud Storage, which keeps large files out of your API servers.

### Filestore and NetApp Volumes
`working` · Related: Block vs file vs object storage
**What:** Managed NFS file shares (Filestore tiers: Basic, Zonal, Regional, Enterprise). NetApp Volumes adds SMB and NetApp features. Used for lift-and-shift apps needing a shared POSIX filesystem, GKE ReadWriteMany volumes, and some ML training data.

### Durability vs availability
`core` · Related: Replication, SLA
**What:** **Durability:** the probability your data isn't *lost* (for example 11 nines). **Availability:** the proportion of time you can *access* it (for example 99.95%). Data can be perfectly durable and temporarily unavailable.
**Watch out:** Durability doesn't protect against *you* deleting or corrupting data. That's what versioning, soft delete, backups and PITR are for.

### OLTP vs OLAP
`core` · Related: Row vs columnar storage, BigQuery, Cloud SQL
**What:** **OLTP** (online transaction processing): many small, concurrent reads and writes of individual records, with low latency and strict consistency. Bank ledgers, payments, customer profiles. **OLAP** (online analytical processing): fewer, huge queries scanning and aggregating millions or billions of rows. Reporting, risk, ML features.
**GCP:** OLTP: Cloud SQL, AlloyDB, Spanner, Firestore, Bigtable (key lookups). OLAP: BigQuery. **HTAP** (both) features: AlloyDB's columnar engine, Spanner Data Boost, BigQuery federated queries to Spanner and Cloud SQL.

### Row vs columnar storage
`core` · Related: OLTP vs OLAP, BigQuery
**What:** **Row stores** keep each record's fields together, so fetching or updating one record is fast (OLTP). **Columnar stores** keep each column together, so scanning a few columns over many rows is fast, and the data compresses very well (OLAP).
**Watch out:** That's why `SELECT *` on BigQuery is expensive (you pay for every column scanned) and why BigQuery isn't a transactional database.

### ACID transactions
`core` · Related: Isolation levels, Spanner, Cloud SQL
**What:** **Atomicity** (all or nothing), **Consistency** (constraints hold before and after), **Isolation** (concurrent transactions don't see each other's partial work), **Durability** (committed means it survives crashes).
**GCP:** Cloud SQL, AlloyDB and Spanner are fully ACID (Spanner even across regions). Firestore has ACID transactions over documents. Bigtable gives single-row atomicity only. BigQuery supports multi-statement transactions but isn't built for OLTP.

### Isolation levels and anomalies
`working` · Related: ACID transactions, Consistency models
**What:** How strongly concurrent transactions are separated. **Read committed** (the default in PostgreSQL) prevents dirty reads, but non-repeatable reads and phantoms can happen. **Repeatable read / snapshot isolation**: a stable snapshot, but *write skew* is possible. **Serializable**: as if transactions ran one after another (the safest, with more conflicts and retries).
**GCP:** Spanner defaults to serializable (with strict "external consistency"). For money movement, know which level you're running at, and handle retries on conflicts.

### Consistency models
`core` · Related: CAP and PACELC, Replication
**What:** What readers are guaranteed to see after a write. **Strong / linearizable:** every read sees the latest committed write. **Eventual:** replicas converge over time, so a read may be stale. In between: **read-your-writes**, **monotonic reads**, **bounded staleness**.
**GCP:** Strong: Cloud Storage, Spanner, Firestore, Cloud SQL primary, and Bigtable within a single cluster. Eventual: Cloud SQL read replicas, Bigtable cross-cluster replication, caches. Spanner offers **stale reads** (bounded or exact staleness) for lower latency when slightly old data is fine.
**Watch out:** Reading from an async replica right after writing to the primary returns old data, a classic bug in "read-replica for scale" designs.

### CAP theorem and PACELC
`working` · Related: Consistency models, Spanner
**What:** **CAP:** during a network **P**artition, a distributed system must choose **C**onsistency (reject or block some requests) or **A**vailability (answer, possibly with stale data). **PACELC** extends it: **E**lse (normally), choose between **L**atency and **C**onsistency.
**GCP:** Spanner chooses consistency, and gets very high availability by running on Google's redundant private network and TrueTime. Bigtable multi-cluster and caches choose availability and latency.

### Replication (sync vs async, leader/follower)
`core` · Related: High availability, RPO, Cloud SQL, Spanner
**What:** Keeping copies of data on multiple nodes or locations. **Synchronous:** a write is acknowledged only when the replicas have it, so **RPO = 0**, but write latency includes the slowest replica (fine within a region, painful across distant regions). **Asynchronous:** acknowledge first, replicate later, so writes are fast, but **RPO > 0** (recent writes can be lost on failover) and replicas lag.
**How:** **Leader/follower** (single writer, many readers), **multi-leader** (conflict resolution needed), **consensus (Paxos/Raft)** (a majority quorum agrees, as in Spanner).
**GCP:** Cloud SQL HA uses synchronous replication to a standby in another zone. Read replicas and cross-region replicas are async. Spanner uses Paxos-based synchronous replication across zones or regions. Regional Persistent Disk replicates synchronously across 2 zones.

### Sharding and partitioning
`core` · Related: Spanner, Bigtable, BigQuery partitioning
**What:** Splitting data across nodes by key so that storage and throughput scale horizontally. **Range** sharding (contiguous key ranges) or **hash** sharding.
**How:** A good key spreads load evenly. **Hotspots** happen when keys are sequential (timestamps, auto-increment IDs), because all new writes hit one shard.
**GCP:** Spanner and Bigtable split data by key range automatically. Avoid monotonically increasing leading keys: use UUIDv4, bit-reversed sequences, or a hashed or salted prefix. BigQuery "partitioning" is a related but different idea: it splits tables (usually by date) to prune scans.

### Indexes
`working` · Related: OLTP vs OLAP, Firestore
**What:** Data structures (B-trees mostly, plus hash, GIN, vector indexes) that make lookups by a column fast, at the cost of write overhead and storage.
**GCP:** Cloud SQL, AlloyDB and Spanner have secondary indexes. Firestore needs an index for every query (single-field indexes are automatic, composite ones you define). Bigtable has only the row key, so design your key around your queries. Vector indexes: ScaNN (AlloyDB), HNSW/IVF (pgvector), Vector Search.

### Normalization, denormalization and star schemas
`working` · Related: BigQuery, Data warehouse
**What:** **Normalization:** split data into related tables to avoid duplication and update anomalies (OLTP). **Denormalization:** duplicate data or nest it to avoid joins (analytics, NoSQL). A **star schema** has central *fact* tables (events, transactions) joined to *dimension* tables (customer, product, date).
**GCP:** BigQuery handles star schemas well, and it also rewards **nested and repeated fields** (STRUCT/ARRAY), which store child records inside the parent row to avoid joins.

### Cloud SQL
`core` · Related: Replication, Backup and PITR, Connection pooling
**What:** Managed MySQL, PostgreSQL and SQL Server. Google handles provisioning, patching, backups, replication and failover.
**How:** **HA configuration:** a primary plus a standby in another zone of the same region, with synchronous storage-level replication and automatic failover (about a minute). **Read replicas** (async, same or cross-region) can be promoted for DR. Automated backups + **point-in-time recovery** (PITR, from transaction logs). **Private IP** (through PSA or PSC) and the **Cloud SQL Auth Proxy** / language connectors (IAM-authorized, TLS, no allow-listing IPs). **IAM database authentication**. Maintenance windows. **Editions:** Enterprise and **Enterprise Plus** (better performance, near-zero-downtime maintenance, 99.99% SLA, larger data cache). It scales **vertically**, with storage up to tens of TB.
**GCP:** The default for "a normal relational app database" and lift-and-shift of MySQL, PostgreSQL or SQL Server.

### AlloyDB for PostgreSQL
`core` · Related: Cloud SQL, Vector search, HTAP
**What:** A PostgreSQL-compatible database built by Google with compute separated from a distributed, log-based storage layer.
**How:** Faster transactional throughput than standard PostgreSQL, a **columnar engine** for fast analytics on live data, **read pools** for scaling reads, a 99.99% SLA, cross-region secondary clusters for DR, and **AlloyDB AI**: **pgvector with ScaNN indexes**, in-database calls to embedding and Gemini models, natural-language-to-SQL. AlloyDB Omni runs it anywhere (on-prem, other clouds).
**GCP:** Strong choice for demanding PostgreSQL workloads and for RAG, where you want vectors, metadata filters and transactional data in one place.

### Spanner
`core` · Related: CAP and PACELC, TrueTime, Sharding
**What:** A globally distributed relational database with **horizontal scale**, **strong external consistency** and up to **99.999% availability** (multi-region configurations; 99.99% regional).
**How:** Data is split by primary-key ranges across servers, and each split is replicated with **Paxos** across zones or regions. **TrueTime** (GPS- and atomic-clock-backed time with bounded uncertainty) gives globally ordered commit timestamps. It offers GoogleSQL or a PostgreSQL interface, interleaved tables (child rows stored with the parent), change streams, **Data Boost** (analytics without hurting OLTP), graph and vector search, full-text search. Capacity is measured in nodes or processing units, with autoscaling and editions.
**Watch out:** Hotspotting from sequential keys. Cost is higher than Cloud SQL, so justify it with scale or availability needs (core banking ledgers, payments, global consistency).

### TrueTime
`aware` · Related: Spanner
**What:** Google's clock API that returns a time *interval* guaranteed to contain true time, using GPS and atomic clocks in each data centre. Spanner waits out the uncertainty at commit ("commit wait") so timestamps reflect real-time order everywhere.

### Firestore
`core` · Related: Serverless, Consistency models, Indexes
**What:** A serverless, autoscaling **document database**. **Collections** contain **documents** (JSON-like, nested), which can contain subcollections.
**How:** Strongly consistent reads and queries, ACID transactions, **real-time listeners** (clients get pushed updates), offline SDKs for mobile and web, security rules for direct client access, TTL policies, PITR, and regional or multi-region locations (99.999% multi-region SLA). Two modes: **Native** (the full feature set) and **Datastore mode** (server-side, for the legacy Datastore API). Firestore also offers MongoDB compatibility and vector search.
**Watch out:** Every query needs an index. There are write-rate limits per document (about 1 sustained write per second per document) and sequential-ID hotspots.

### Bigtable
`core` · Related: Sharding, Time-series data, HBase
**What:** A wide-column NoSQL store for **massive throughput and single-digit millisecond latency** at TB–PB scale. It's the technology behind Search, Maps and Analytics.
**How:** Each row has one **row key**, and the table is sorted by it. Columns are grouped into **column families**. Cells are versioned by timestamp. It offers single-row transactions only, no secondary indexes (beyond limited new features) and an HBase-compatible API. Clusters are made of nodes (throughput scales roughly linearly). **Replication** across clusters and regions is *eventually consistent*, with app profiles that route to one cluster or many.
**GCP:** Used for time series, IoT, market tick data, fraud feature lookups, personalization and ad-tech. Row key design (for example `customerId#reverseTimestamp`) is the whole game.

### Memorystore
`core` · Related: Caching patterns, Stateless services
**What:** Managed in-memory data stores: **Redis** (and Redis Cluster), **Valkey** (the open-source Redis fork) and **Memcached**. Sub-millisecond latency.
**How:** Uses: caching, session state, rate-limit counters, leaderboards (sorted sets), pub/sub, queues, LLM response or semantic caches, vector search. HA with replicas and automatic failover. Private connectivity (PSC). Persistence (RDB/AOF) is optional. It's still memory first, so not a system of record.

### Caching patterns
`core` · Related: Memorystore, CDN, Consistency models
**What:** **Cache-aside** (lazy loading): the app checks the cache, and on a miss reads the DB and fills the cache. **Read-through**: the cache loads from the DB itself. **Write-through**: write to the cache and DB together. **Write-behind**: write to the cache, flush to the DB later (risk of loss). Entries leave through **TTLs** and **eviction** (LRU, LFU).
**How:** Two hard problems: **invalidation** (when the source changes) and **stampedes** (thundering herd, when many misses hit the DB at once; fixed by request coalescing, jittered TTLs, early refresh).
**GCP:** Memorystore (application cache), Cloud CDN (edge), BigQuery result cache and BI Engine, LLM **context caching** (cache long prompts on the model side) and **semantic caching** (reuse answers to similar questions, through Apigee or a vector cache).

### BigQuery
`core` · Related: OLAP, Partitioning and clustering, BigQuery slots and editions
**What:** A serverless, petabyte-scale data warehouse with separate storage and compute and standard SQL. It's also the hub of GCP analytics and AI.
**How:** **Storage:** columnar (Capacitor format) on Colossus, organized as project → **dataset** (location-bound, the main access boundary) → tables and views. **Compute:** the Dremel query engine allocates **slots** (units of compute). **Pricing:** on-demand (per TB scanned) or **capacity** (editions with reservations and autoscaling slots). Ingestion: free batch loads, the **Storage Write API** (streaming, exactly-once), Pub/Sub BigQuery subscriptions, Datastream (CDC), Data Transfer Service. Features: partitioning and clustering, **materialized views**, **BI Engine** (in-memory acceleration), **search indexes**, **vector search**, **BigQuery ML** (train or call models, including Gemini, in SQL), **remote functions** (call Cloud Run from SQL), **time travel** (7 days) and **fail-safe**, **authorized views and datasets**, **row-level security**, **column-level security with policy tags** (and dynamic data masking), **Analytics Hub** (data sharing), **BigLake / external tables** (query GCS data in Iceberg or Parquet), multi-statement transactions.
**Watch out:** It isn't for OLTP or point lookups at high QPS. Costs come from scanning (on-demand), so partition, cluster, avoid `SELECT *`, and set custom quotas or maximum bytes billed.

### BigQuery partitioning and clustering
`core` · Related: BigQuery, Sharding
**What:** **Partitioning** splits a table into segments by a date or timestamp column, ingestion time, or integer range. Queries that filter on the partition column only scan the matching partitions. **Clustering** sorts the data within partitions by up to 4 columns, so filters and aggregations on those columns read fewer blocks.
**GCP:** You can require a partition filter (`require_partition_filter`) to stop accidental full scans. Partition expiry is a way to implement retention policies.

### BigQuery slots, editions and reservations
`working` · Related: BigQuery, Pricing models
**What:** A **slot** is a virtual CPU for queries. **On-demand** pricing uses a shared pool with a per-project cap. **Editions** (Standard, Enterprise, Enterprise Plus) let you buy slot capacity with **autoscaling** and optional commitments. **Reservations** and **assignments** dedicate capacity to projects or folders (workload isolation: prod ETL separated from ad-hoc analysts).
**Watch out:** Enterprise Plus brings features some regulated workloads need (for example certain compliance controls and managed disaster recovery). Check the edition-feature matrix.

### Data lake, data warehouse and lakehouse
`core` · Related: Cloud Storage, BigQuery, BigLake, Dataplex
**What:** **Data lake:** cheap object storage holding raw data in any format (schema-on-read). **Warehouse:** curated, structured, governed tables optimized for SQL (schema-on-write). **Lakehouse:** warehouse-style governance, transactions and performance on open table formats (**Apache Iceberg**, Delta, Hudi) in object storage, readable by many engines (BigQuery, Spark, Trino).
**GCP:** **BigLake** gives unified, fine-grained governance over GCS data and BigQuery, including BigLake Iceberg tables and a metastore. Common layering: raw/bronze → cleaned/silver → curated/gold.

### Dataplex Universal Catalog (data governance)
`working` · Related: Data lake, Sensitive Data Protection, Lineage
**What:** GCP's data governance layer: a **catalog** (search and metadata across BigQuery, GCS, databases and AI assets), **business glossary**, **data lineage** (column-level lineage across BigQuery, Dataflow, Composer and others), **data quality** scans and **data profiling**, and lake/zone management with security policies.
**GCP:** It answers the regulator's questions "where did this number come from?" (lineage, as in BCBS 239 risk-data aggregation) and "who owns this dataset and what's in it?".

### Backup, PITR and Backup and DR Service
`core` · Related: RPO and RTO, Disaster recovery
**What:** **Backups** are copies taken at intervals. **Point-in-time recovery (PITR)** replays transaction logs to restore to any second within a window. **Backup and DR Service** is GCP's centralized backup management (VMs, databases, file systems, GKE) with **backup vaults** that are immutable and indelible (protection against ransomware and insiders).
**GCP:** Cloud SQL (automated backups + PITR), AlloyDB (continuous backup + PITR), Spanner (backups + PITR up to 7 days), Firestore (PITR + scheduled backups), BigQuery (time travel + snapshots), GKE (Backup for GKE).
**Watch out:** A backup you've never restored is a hope, not a control. Test restores, and measure the real RTO.

### Database Center
`aware` · Related: Cloud SQL, AlloyDB, Spanner
**What:** A fleet-wide dashboard for all your GCP databases (inventory, health, security and configuration issues, recommendations), with AI-assisted insights.

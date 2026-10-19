# 07 · Data processing, messaging and analytics pipelines

How data moves: batch and streaming, queues and logs, pipelines and orchestration.

---

### Batch vs streaming
`core` · Related: Dataflow, Pub/Sub, Windowing
**What:** **Batch** processes a bounded dataset on a schedule (nightly risk runs, end-of-day reconciliations): simpler, cheaper, with higher latency. **Streaming** processes an unbounded flow of events continuously, with seconds of latency (fraud detection, real-time dashboards, alerts): harder, because of ordering, late data and state.
**GCP:** Batch: BigQuery SQL, Dataflow batch, Dataproc, Cloud Run jobs, Batch. Streaming: Pub/Sub or Kafka → Dataflow → BigQuery or Bigtable, or BigQuery continuous queries.

### ETL vs ELT
`core` · Related: BigQuery, Dataform, Dataflow
**What:** **ETL:** extract → transform (in a separate engine) → load the cleaned result. **ELT:** extract → load raw data into the warehouse → transform there with SQL. ELT has become the default with powerful warehouses like BigQuery.
**GCP:** ELT with BigQuery + **Dataform** (version-controlled SQL pipelines) or dbt. ETL with Dataflow, Dataproc or Data Fusion when you need heavy transformation, streaming, or data shaping before it lands (for example PII tokenization before the data reaches the lake).

### Change data capture (CDC)
`core` · Related: Datastream, Transactional outbox, Replication
**What:** Capturing row-level inserts, updates and deletes from a database's transaction log and streaming them elsewhere, without heavy queries on the source.
**GCP:** **Datastream** (serverless CDC from MySQL, PostgreSQL, Oracle, SQL Server and AlloyDB into BigQuery or Cloud Storage), Spanner change streams, Debezium on Kafka. A very common bank pattern: core systems on-prem → CDC → BigQuery for analytics and ML features.

### Queue vs pub/sub vs event log (stream)
`core` · Related: Pub/Sub, Kafka, Cloud Tasks
**What:** **Queue:** each message goes to *one* consumer from a pool (work distribution), and is deleted once processed. **Pub/sub:** each message is copied to *every subscription* (fan-out), and each subscription is a queue for its consumers. **Event log / stream (Kafka-style):** an ordered, retained, append-only log split into partitions. Consumers track their own **offset** and can replay from any point.
**GCP:** Pub/Sub is pub/sub with per-subscription queues, plus retention and seek for replay. Managed Service for Apache Kafka is the log model. Cloud Tasks is a queue of HTTP calls to one target.

### Pub/Sub
`core` · Related: Delivery semantics, Dead-letter topics, Eventarc
**What:** A global, serverless, autoscaling messaging service. Publishers send to **topics**, and **subscriptions** deliver to subscribers.
**How:** Subscription types: **pull** (StreamingPull for high throughput), **push** (HTTPS POST to an endpoint, for example Cloud Run, with OIDC authentication), **BigQuery** (writes straight into a table), **Cloud Storage** (batches into files). Delivery: messages are redelivered until **acked**, within an **ack deadline** that can be extended. Other features: **retention** (7 days by default, longer configurable; topic retention allows replay), **seek** (replay to a timestamp or snapshot), **ordering keys** (in order per key, within a region), **exactly-once delivery** (pull, per region), **dead-letter topics**, **filtering** (by attributes), **schemas** (Avro or Protobuf), **message storage policy** (restrict which regions store messages, which matters for UK residency), **single message transforms**, CMEK. Throughput scales automatically.
**Watch out:** Pub/Sub is a *global* service by default. Set the message storage policy (or use regional endpoints) when data must stay in the UK.

### Delivery semantics (at-most / at-least / exactly once)
`core` · Related: Idempotency, Pub/Sub, Dataflow
**What:** **At-most-once:** may lose messages, never duplicates. **At-least-once:** never loses, may duplicate. This is the norm. **Exactly-once:** each message has its effect exactly once, which in practice means at-least-once delivery + deduplication or idempotent processing.
**GCP:** Pub/Sub is at-least-once by default, with an exactly-once option for pull subscriptions. Dataflow gives exactly-once *processing* inside the pipeline. BigQuery Storage Write API gives exactly-once writes with offsets.
**Watch out:** End-to-end exactly-once needs your *sink* to be idempotent too. Assume duplicates.

### Message ordering
`working` · Related: Pub/Sub, Kafka, Sharding
**What:** Guaranteeing consumers see related messages in the order they were published.
**How:** Global ordering doesn't scale, so systems order **per key**: Pub/Sub ordering keys, Kafka partitions. A failure (an unacked message) blocks later messages for that key until it's resolved.
**Watch out:** Ask whether you really need ordering, or whether you can use versioning or timestamps and idempotent "last write wins" instead.

### Dead-letter topics and poison messages
`working` · Related: Pub/Sub, Retries and backoff
**What:** A **poison message** fails processing every time (bad format, a bug) and would block or loop forever. A **dead-letter topic (DLT/DLQ)** receives messages after N failed delivery attempts, so the rest keep flowing, and someone can inspect or replay them later.
**GCP:** Pub/Sub subscriptions take `--dead-letter-topic` and `--max-delivery-attempts`. The Pub/Sub service agent needs publisher and subscriber roles for this. Alert on DLT backlog.

### Apache Kafka and Managed Service for Apache Kafka
`working` · Related: Queue vs pub/sub vs event log, Pub/Sub
**What:** **Kafka** is the open-source distributed event-log platform: topics split into **partitions** (ordered, replicated), producers, **consumer groups** (each partition is consumed by one member of the group), offsets, retention by time or size, a connector ecosystem (Kafka Connect) and stream processing (Kafka Streams).
**GCP:** **Google Cloud Managed Service for Apache Kafka** runs Kafka clusters for you. Choose it when you have Kafka skills, Kafka-native tools (Debezium, Connect) or multicloud portability needs. Choose Pub/Sub for serverless simplicity and native GCP integration.

### Dataflow and Apache Beam
`core` · Related: Batch vs streaming, Windowing and watermarks, Pub/Sub
**What:** **Apache Beam** is a unified programming model (Java, Python, Go, SQL, YAML) for batch *and* streaming pipelines. **Dataflow** is Google's serverless runner for Beam.
**How:** Pipelines are graphs of **PCollections** (datasets) and **transforms** (ParDo, GroupByKey, Combine, windowing). Dataflow handles autoscaling workers, **Streaming Engine**, dynamic work rebalancing, exactly-once processing, **templates** (Classic or Flex, for reusable launches), Dataflow Prime, and GPUs for ML inference in pipelines. Common sources and sinks: Pub/Sub, Kafka, GCS, BigQuery, Bigtable, Spanner, JDBC.
**GCP:** The standard engine for streaming ETL, real-time feature computation (fraud), and large batch transforms. Enrichment and ML inference (RunInference) can run inside the pipeline.

### Windowing, watermarks and late data
`working` · Related: Dataflow, Batch vs streaming
**What:** Ways to aggregate an unbounded stream. **Windows** group events by **event time**: **fixed / tumbling** (every 5 minutes), **sliding** (5-minute windows every minute), **session** (bursts separated by gaps). A **watermark** is the system's estimate of "we've probably seen all events up to time T". **Triggers** decide when to emit results (at the watermark, early speculative results, late updates). **Allowed lateness** controls how long late events can still update a window.
**Watch out:** Event time (when it happened) ≠ processing time (when you saw it). Mobile and on-prem sources often deliver late. Correct streaming results depend on handling this.

### Dataproc
`working` · Related: Dataflow, Data lake
**What:** Managed **Apache Spark** and Hadoop ecosystem (Hive, Presto/Trino, Flink). Clusters start in about 90 seconds. **Dataproc Serverless** runs Spark batches and interactive sessions without clusters.
**How:** Best practice: **ephemeral, job-scoped clusters**, with data in **Cloud Storage** (not HDFS) and metadata in a shared metastore. Use autoscaling and Spot secondary workers.
**GCP:** Choose it to migrate existing Spark or Hadoop jobs, or for Spark skills and libraries. Choose Dataflow for new serverless pipelines, especially streaming.

### Cloud Composer (Apache Airflow)
`working` · Related: Workflows, Orchestration vs choreography
**What:** Managed **Apache Airflow** for orchestrating data pipelines as **DAGs** (directed acyclic graphs) of tasks, with operators for BigQuery, Dataflow, Dataproc, GCS, external systems, retries, SLAs, backfills and scheduling.
**Watch out:** Composer *orchestrates*: it triggers and monitors work done elsewhere. Don't do heavy processing inside Airflow workers. For lightweight orchestration of API calls and services, use **Workflows**.

### Dataform
`working` · Related: ETL vs ELT, BigQuery
**What:** Develops, version-controls (git), tests and schedules **SQL transformation pipelines in BigQuery** (SQLX files with dependencies, assertions for data quality, incremental tables). Comparable to dbt, and native to BigQuery.

### Cloud Data Fusion
`aware` · Related: ETL vs ELT
**What:** A visual, low-code ETL/ELT designer (based on open-source CDAP) with many connectors. Pipelines run on Dataproc. Suits teams that prefer GUI-built integrations.

### Data transfer and ingestion services
`working` · Related: Migration, Cloud Storage, BigQuery
**What:** **Storage Transfer Service:** bulk and scheduled transfers into GCS from other clouds, HTTP sources, on-prem file systems (through agents) or between buckets. **Transfer Appliance:** a physical device shipped to you for offline transfer of hundreds of TB to PB. **BigQuery Data Transfer Service:** scheduled loads from SaaS (Google Ads, Salesforce and others), other warehouses (Teradata, Redshift migrations) and GCS. **`gcloud storage`:** command-line copies.
**Watch out:** Rule of thumb: when bandwidth × time-window is less than the data size, use the appliance.

### Looker and Looker Studio
`working` · Related: BigQuery, Semantic layer
**What:** **Looker:** an enterprise BI platform with a governed **semantic layer** (LookML defines metrics once), embedded analytics and APIs. **Looker Studio:** free, self-service dashboards and reports with many connectors.
**GCP:** Banks prefer Looker, because consistent, governed metric definitions matter for regulatory reporting. The semantic layer also grounds natural-language-to-data agents ("conversational analytics").

### BigQuery continuous queries and real-time analytics
`aware` · Related: Batch vs streaming, BigQuery
**What:** **Continuous queries** run SQL on data as it streams into BigQuery and export results continuously to Pub/Sub, Bigtable or other tables (for example real-time alerting with SQL only). Together with Storage Write API ingestion, BigQuery can handle near-real-time use cases without Dataflow.

### Data mesh and federated governance
`aware` · Related: Dataplex, Data products
**What:** An organizational approach where **domain teams own their data as products** (with SLAs, documentation and quality), on a self-service platform, under **federated computational governance** (global standards enforced automatically).
**GCP:** Often built with domain-owned projects and datasets, Dataplex for catalog and governance, Analytics Hub for sharing, and BigLake for shared lake storage.

### Data quality and validation
`aware` · Related: Dataplex, Dataform
**What:** Checks that data is complete, valid, unique, timely and consistent. In pipelines: schema enforcement, assertions (Dataform), Dataplex data-quality scans, Great Expectations-style tests, and quarantining bad records rather than failing everything.

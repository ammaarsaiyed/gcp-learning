# Day 3: Data and Integration

**Lenses:** 4 Data · 5 Integration
**Today's question:** *Where does state live, and how do the parts talk without being tightly coupled?*

---

## Read (40 min)

### 3.1 Picking storage: the decision in 3 questions

```
1. What SHAPE is the data?
   ├─ Files/blobs (images, backups, logs, data lake) ─────────────► Cloud Storage
   ├─ A disk for a VM ────────────────────────────────────────────► Persistent Disk / Hyperdisk
   ├─ Shared POSIX file system (NFS) ─────────────────────────────► Filestore
   └─ Structured records ─► go to 2
2. Is it for TRANSACTIONS (the app) or ANALYTICS (questions over lots of data)?
   ├─ Analytics, SQL over GB–PB ──────────────────────────────────► BigQuery
   └─ Transactions ─► go to 3
3. Relational (SQL, joins, strict schema) or not?
   ├─ Relational
   │   ├─ Standard app, one region, up to tens of TB ─────────────► Cloud SQL (MySQL/Postgres/SQL Server)
   │   ├─ Postgres needing more performance / mixed analytics ────► AlloyDB
   │   └─ Global scale, horizontal writes, 99.999% ───────────────► Spanner
   └─ Non-relational
       ├─ Documents, mobile/web apps, serverless, real-time sync ─► Firestore
       ├─ Huge throughput, time series/IoT, single-key lookups ───► Bigtable
       └─ Sub-millisecond cache / sessions / leaderboards ────────► Memorystore (Redis/Valkey)
```

Exam-style tells: **"global" + "strongly consistent" + "relational"** → Spanner. **"Petabytes" + "SQL analytics"** → BigQuery. **"IoT/time series" + "millions of writes per second"** → Bigtable. **"Lift and shift MySQL"** → Cloud SQL.

### 3.2 Cloud Storage (GCS)

- **Buckets** (globally unique names) hold **objects** (immutable; you overwrite, you don't edit). Flat namespace; "folders" are just name prefixes.
- **Location:** region, dual-region or multi-region. That choice trades availability and latency against cost.
- **Storage classes** (all have millisecond access; colder means cheaper storage but retrieval fees and a minimum storage duration):

  | Class | Minimum duration | Use for |
  |---|---|---|
  | Standard | none | Hot data, serving |
  | Nearline | 30 days | Accessed about once a month |
  | Coldline | 90 days | About once a quarter |
  | Archive | 365 days | Compliance archives, DR |

- **Lifecycle rules** move objects to colder classes or delete them by age. **Autoclass** does it automatically.
- **Access:** use **uniform bucket-level access** (IAM only, no per-object ACLs). **Signed URLs** give temporary access to one object without IAM. **Public access prevention** blocks accidental public exposure.
- **Protection:** object versioning, soft delete, retention policies and bucket lock (WORM).

### 3.3 Relational database essentials

- **Cloud SQL:** managed MySQL/Postgres/SQL Server. **HA** = a regional instance with a standby in another zone and automatic failover. **Read replicas** scale reads (including cross-region for DR). Automated backups and point-in-time recovery. Scales up (bigger machine), not out.
- Connect privately: **private IP** in your VPC + the **Cloud SQL Auth Proxy** or language connectors (IAM-based, encrypted). Store credentials in Secret Manager or use IAM database authentication.
- **AlloyDB:** Postgres-compatible, much faster for transactions and analytics, with pgvector for AI.
- **Spanner:** relational and SQL, scales horizontally, strong consistency across regions, up to 99.999% availability. More expensive, so use it when you really need global scale.

### 3.4 BigQuery: the analytics engine

- **Serverless warehouse:** no cluster. Storage and compute are separate. Columnar storage.
- **Hierarchy:** project → **dataset** (has a location; it's the unit of access control) → **table** / view.
- **Cost model:** on-demand pricing charges **per byte scanned**, or you buy capacity (slots, through editions). So:
  - **Never `SELECT *`.** Columnar storage means you pay for the columns you read.
  - **Partition** tables (usually by date) and **cluster** them (by commonly filtered columns) to scan less.
  - `--dry_run` shows bytes scanned before you run a query.
- Gets data in through batch loads (free), streaming (Storage Write API), **Pub/Sub BigQuery subscriptions**, Dataflow, or **federated queries** against GCS/Cloud SQL without loading.
- Extras: BigQuery ML (models in SQL), vector search, and BI through Looker / Looker Studio.

### 3.5 Integration: decoupling services

**Pub/Sub** is the backbone. A **publisher** sends a message to a **topic**. Each **subscription** on the topic gets its own copy (fan-out).

```
                       ┌─► subscription A (pull)   ─► worker on GKE
publisher ─► TOPIC ────┼─► subscription B (push)   ─► Cloud Run URL
                       └─► subscription C (BigQuery) ─► table (no code!)
```

- **At-least-once delivery.** Consumers must be **idempotent** (handle duplicates). Exactly-once is available for pull subscriptions. Ordering keys give per-key ordering.
- Unacked messages are retried, and **dead-letter topics** catch poison messages. Messages are retained for 7 days by default.
- It's global, autoscaling and serverless. It buffers spikes, so the producer doesn't wait on the consumer.

**Which glue service?**

| Need | Use |
|---|---|
| Fan-out events or streaming messages between services | **Pub/Sub** |
| "When X happens in GCP (file uploaded, audit log entry), call my service" | **Eventarc** (uses Pub/Sub under the hood) |
| Run something on a schedule (cron) | **Cloud Scheduler** |
| Queue of HTTP calls with rate limits, retries and delays, aimed at one target | **Cloud Tasks** |
| Multi-step process: call A, then B, branch, wait, retry | **Workflows** |
| Large-scale streaming or batch data transformation | **Dataflow** (Apache Beam) |
| Existing Spark/Hadoop jobs | **Dataproc** |
| Orchestrate data pipelines with dependencies (DAGs) | **Cloud Composer** (Airflow) |
| Replicate database changes (CDC) into BigQuery | **Datastream** |

---

## Lab (80 min)

Today the API gets a database, an event stream and an analytics sink:

```
 curl ─► Cloud Run (notes-api) ─┬─► Firestore            (source of truth)
                                ├─► Pub/Sub: note-events ─► BigQuery subscription ─► gcpweek.notes_raw
                                └─► Cloud Storage bucket (uploads)
```

```bash
source ~/gcpweek.env && gcloud config set project "$PROJECT_ID"
gcloud services enable firestore.googleapis.com pubsub.googleapis.com bigquery.googleapis.com
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
```

### Core A: Firestore, plus watching IAM fail first (20 min)

```bash
gcloud firestore databases create --location="$REGION"     # the "(default)" database, Native mode

# Call the API BEFORE granting access, on purpose
curl -s -X POST "$URL/notes" -H "Content-Type: application/json" -d '{"text":"first note"}'
#   → 500 Internal Server Error. Find out why:
#   (logs can take about 30s to show up)
gcloud logging read 'resource.type="cloud_run_revision" AND textPayload:"PermissionDenied"' \
  --limit=1 --freshness=10m --format='value(textPayload)' | tail -3
#   The service account has no Firestore permission. Least privilege is working.

# Grant exactly what is needed (Firestore has no per-collection IAM, so this is project level)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$APP_SA" --role="roles/datastore.user"
sleep 60    # IAM changes take up to a minute or two to propagate

curl -s -X POST "$URL/notes" -H "Content-Type: application/json" -d '{"text":"first note"}'
curl -s "$URL/notes"
```

Look at the data in the Console under Firestore → Data.

### Core B: Pub/Sub → BigQuery with no consumer code (25 min)

```bash
# Analytics sink: a dataset and a table with one STRING column named "data"
bq --location="$REGION" mk --dataset "$PROJECT_ID:gcpweek"
bq mk --table "$PROJECT_ID:gcpweek.notes_raw" data:STRING

# The topic, and resource-level IAM: the app may publish to THIS topic only
gcloud pubsub topics create note-events
gcloud pubsub topics add-iam-policy-binding note-events \
  --member="serviceAccount:$APP_SA" --role="roles/pubsub.publisher"

# The Pub/Sub SERVICE AGENT (Google's identity for Pub/Sub) needs to write to BigQuery
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# A BigQuery subscription: Pub/Sub writes each message into the table
gcloud pubsub subscriptions create note-events-to-bq --topic=note-events \
  --bigquery-table="$PROJECT_ID:gcpweek.notes_raw"

# A second, pull subscription on the same topic to see fan-out
gcloud pubsub subscriptions create note-events-debug --topic=note-events

# Tell the app about the topic (creates a new revision; config is part of a revision)
gcloud run services update notes-api --region="$REGION" --update-env-vars=TOPIC=note-events

for t in "buy milk" "learn VPCs" "draw the 8 lenses"; do
  curl -s -X POST "$URL/notes" -H "Content-Type: application/json" -d "{\"text\":\"$t\"}"; echo
done

gcloud pubsub subscriptions pull note-events-debug --limit=5 --auto-ack   # copy #1 of each message
bq query --project_id="$PROJECT_ID" --use_legacy_sql=false \
  'SELECT JSON_VALUE(data, "$.text") AS text, JSON_VALUE(data, "$.created_at") AS created_at
   FROM gcpweek.notes_raw ORDER BY created_at DESC'                        # copy #2, already in the warehouse
```

Think about it: the API doesn't know BigQuery exists. Tomorrow you could add a third subscription (an email notifier, say) without touching the API. That's what decoupling means.

### Core C: Cloud Storage with lifecycle rules (15 min)

```bash
export BUCKET="${PROJECT_ID}-uploads"
echo "export BUCKET=$BUCKET" >> ~/gcpweek.env
gcloud storage buckets create "gs://$BUCKET" --location="$REGION" --uniform-bucket-level-access

# Least privilege on ONE bucket: the app can create objects but not read or delete them
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" \
  --member="serviceAccount:$APP_SA" --role="roles/storage.objectCreator"

cat > /tmp/lifecycle.json <<'EOF'
{"rule": [
  {"action": {"type": "SetStorageClass", "storageClass": "NEARLINE"}, "condition": {"age": 30}},
  {"action": {"type": "Delete"}, "condition": {"age": 365}}
]}
EOF
gcloud storage buckets update "gs://$BUCKET" --lifecycle-file=/tmp/lifecycle.json

gcloud run services update notes-api --region="$REGION" --update-env-vars=BUCKET="$BUCKET"
echo "hello from day 3" > /tmp/hello.txt
curl -s -F "file=@/tmp/hello.txt" "$URL/upload"
gcloud storage ls -l "gs://$BUCKET/uploads/"
```

### Core D: BigQuery cost awareness (10 min)

```bash
Q='SELECT name, SUM(number) AS total FROM `bigquery-public-data.usa_names.usa_1910_2013`
   GROUP BY name ORDER BY total DESC LIMIT 10'
bq query --use_legacy_sql=false --dry_run "$Q"        # bytes scanned BEFORE running = the cost
bq query --use_legacy_sql=false "$Q"
bq query --use_legacy_sql=false --dry_run \
  'SELECT * FROM `bigquery-public-data.usa_names.usa_1910_2013`'   # compare: SELECT * reads every column
```

### Stretch

- Add an **Eventarc** trigger so that a file uploaded to the bucket calls a second Cloud Run service. Read the Eventarc quickstart for Cloud Storage events and adapt it.
- Add a **dead-letter topic** to `note-events-debug` (`--dead-letter-topic`, `--max-delivery-attempts`).
- Read (don't build) the Cloud SQL "Connect from Cloud Run" guide. Write down the 3 pieces: private IP or Auth Proxy, a service account with `roles/cloudsql.client`, and the password in Secret Manager.

---

## Recall (25 min)

**Draw:** the storage decision tree from memory. Then draw today's lab architecture and label each arrow with the IAM role that allows it.

**Answer:**
1. A global retail app needs a relational database with strongly consistent writes across continents. Which one?
2. Clickstream from 10M users goes to dashboards and SQL analysis. Which services?
3. IoT sensors write 500k readings a second, and you look up by device and time. Which database?
4. Nearline vs Archive: what's the difference in access latency? (A trick question.)
5. Why should Pub/Sub consumers be idempotent?
6. Cloud Tasks vs Pub/Sub: when do you use each?
7. Two ways to cut BigQuery query cost.
8. In the lab, why did the *Pub/Sub service agent* need a BigQuery role, and not the app's service account?

<details><summary>Answers</summary>

1. Spanner.
2. Pub/Sub (ingest) → Dataflow (optional transform) → BigQuery → Looker / Looker Studio. Or a direct Pub/Sub BigQuery subscription.
3. Bigtable.
4. None. All GCS classes have millisecond access. They differ in storage price, retrieval fees and minimum storage duration.
5. Delivery is at-least-once, so duplicates can happen.
6. Pub/Sub: fan-out and decoupled events, where the publisher doesn't know the consumers. Cloud Tasks: explicit calls to one target with rate limiting, scheduling and retries.
7. Select only the columns you need; partition and cluster tables (filter on the partition column). Also: dry-run first, use capacity pricing for steady heavy use.
8. Pub/Sub itself writes to BigQuery, acting as its service agent. The app only publishes to the topic.
</details>

## Work tie-in

- List your team's data stores: `gcloud sql instances list`, `gcloud firestore databases list`, `bq ls`, `gcloud storage ls`. Put each one on the decision tree. Would you have picked the same?
- Find a Pub/Sub topic at work (`gcloud pubsub topics list`). Who publishes, and what subscribes?
- If you build agents: where is session or memory state stored? Where would you send agent events for analytics?

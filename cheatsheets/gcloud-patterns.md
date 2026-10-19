# gcloud Patterns

You don't need to memorize commands. Learn the **grammar** and you can work out the rest.

## The grammar

```
gcloud  <service>  [<group>]  <resource>  <verb>  [NAME]  [--flags]
gcloud  compute               instances   create  web-1   --zone=us-central1-a
gcloud  run                   services    describe notes-api --region=us-central1
gcloud  pubsub                topics      add-iam-policy-binding note-events --member=… --role=…
```

- **Verbs are consistent:** `create`, `list`, `describe`, `update`, `delete`, plus `add-iam-policy-binding` / `get-iam-policy` on most resources.
- **Discovery:** `gcloud <service> --help`, `gcloud <service> <resource> --help`, or press TAB in Cloud Shell. `gcloud help -- <keyword>` searches.
- **Location flags:** zonal resources need `--zone`, regional ones need `--region`. Set defaults with `gcloud config set compute/zone|compute/region`. Cloud Run uses its own `--region` (or `gcloud config set run/region`).
- Release tracks: `gcloud alpha …` / `gcloud beta …` hold newer features.

## Config and auth

```bash
gcloud config list                         # current account, project, region
gcloud config set project PROJECT_ID
gcloud config configurations create work   # named profiles: switch with `gcloud config configurations activate`
gcloud auth login                          # you, for gcloud
gcloud auth application-default login      # you, for local code using client libraries (ADC)
gcloud auth print-identity-token           # ID token, for calling private Cloud Run
```

## Output shaping (the most useful skill)

```bash
--format=json | yaml                                   # everything
--format="value(status.url)"                           # one raw value, for scripts
--format="table(name, zone.basename(), status)"        # custom table
--filter="status=RUNNING AND zone~us-central1"         # server- or client-side filter
--flatten="bindings[].members"                         # explode lists (IAM policies)
--limit=10  --sort-by=~creationTimestamp
```

## IAM pattern (the same everywhere)

```bash
# Project level
gcloud projects add-iam-policy-binding PROJECT --member="serviceAccount:SA_EMAIL" --role="roles/X"
# Resource level (preferred: least privilege)
gcloud storage buckets add-iam-policy-binding gs://BUCKET --member=… --role=…
gcloud pubsub topics add-iam-policy-binding TOPIC --member=… --role=…
gcloud secrets add-iam-policy-binding SECRET --member=… --role=…
gcloud run services add-iam-policy-binding SERVICE --region=R --member=… --role=roles/run.invoker
# Who has what?
gcloud projects get-iam-policy PROJECT --flatten="bindings[].members" --format="table(bindings.role, bindings.members)"
# What can I find in this project? (understanding an unfamiliar environment)
gcloud asset search-all-resources --scope=projects/PROJECT --format="table(assetType, name.basename(), location)"
```

## Member prefixes

`user:` · `group:` · `serviceAccount:` · `domain:` · `principal://…` / `principalSet://…` (Workload Identity Federation) · `allUsers` · `allAuthenticatedUsers`

## Other CLIs

| Tool | For | Example |
|---|---|---|
| `bq` | BigQuery | `bq query --use_legacy_sql=false --dry_run 'SELECT …'` · `bq ls` · `bq show DATASET.TABLE` |
| `gcloud storage` | Cloud Storage (replaces `gsutil`) | `gcloud storage cp file gs://b/` · `gcloud storage ls -r gs://b` |
| `kubectl` | GKE | `gcloud container clusters get-credentials C --region R` first |

## Common errors → fix

| Error | Fix |
|---|---|
| `API [x.googleapis.com] not enabled` | `gcloud services enable x.googleapis.com` |
| `PERMISSION_DENIED` / 403 | Who is calling? (`gcloud config list`, or which service account the workload runs as). Grant the narrowest role. Wait about 60s for propagation |
| `The resource … already exists` | Names are unique (globally for projects and buckets) |
| Quota exceeded | IAM & Admin → Quotas, or pick a different region |
| Org policy violation | A guardrail blocks it. You need an exception from the org admins, or a compliant configuration |

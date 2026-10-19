# Day 1: Foundations (Identity, Hierarchy, Billing, Location, `gcloud`)

**Lenses:** 1 Identity · 8 Cost (+ location, which affects everything)
**Today's question:** *Who can do what, to which resource, where, and who pays?*

---

## Read (40 min)

### 1.1 Resource hierarchy

```
Organization (example.com)          ← tied to a Cloud Identity / Workspace domain
├── Folder: Prod
│   ├── Project: shop-prod           ← billing, APIs, IAM, quotas live here
│   │   ├── Cloud Run service
│   │   └── Cloud Storage bucket     ← resources
│   └── Project: data-prod
└── Folder: Non-prod
    └── Project: shop-dev
```

- **Organization:** the root. Org-wide policy lives here.
- **Folders:** group projects by team, environment or business unit. They can be nested.
- **Project:** the working unit. Every resource belongs to exactly one project. A project has 3 identifiers:
  - **Project ID:** globally unique, chosen by you, **immutable**. This is the one you type all the time.
  - **Project name:** a display label you can change.
  - **Project number:** assigned by Google. Shows up in service account emails.
- Personal accounts can have projects with **no org**. That's fine for learning.

**Why it matters:** policies are set *high* and inherited *down*. You give the data team `BigQuery Data Viewer` on the `Prod` folder once, and every current and future project under it gets it.

### 1.2 IAM: the one sentence

> **An allow policy binds a _principal_ to a _role_ on a _resource_.**

| Part | What it is | Examples |
|---|---|---|
| **Principal** (who) | Identity | `user:ana@x.com`, `group:devs@x.com`, `serviceAccount:app@proj.iam.gserviceaccount.com`, `domain:x.com`, `allUsers` (public!) |
| **Role** (what) | A bundle of **permissions** (`service.resource.verb`, for example `storage.objects.get`) | Basic: `roles/owner`, `roles/editor`, `roles/viewer` (**avoid in prod**). Predefined: `roles/storage.objectViewer`. Custom: your own bundle |
| **Resource** (where) | Where the binding is attached | Org, folder, project, or an individual resource (bucket, topic, secret…) |

Rules that matter:
1. **Inheritance is additive.** Effective access = the union of bindings on the resource and all its ancestors.
2. **You can't revoke an inherited grant lower down.** If someone is Editor at the folder, removing them from the project does nothing. (*Deny policies* exist for hard blocks and are checked first.)
3. **Grant to groups, not users.** People join and leave groups. Bindings stay stable.
4. **Least privilege:** use predefined roles at the *lowest* level that works (for example on the bucket, not the project).
5. **Conditions** can restrict a binding (for example only until a date, or only on resources with a certain name prefix).

**IAM vs Organization Policy (people mix these up all the time):**
- **IAM** = *who* can do something.
- **Org Policy** = *what* can be done at all, whoever you are (for example "no external IPs on VMs", "resources only in EU regions", "no public buckets"). Org policy is a guardrail. IAM is a key.

### 1.3 Service accounts (identity for software)

- A service account is **both** an identity (it can hold roles) **and** a resource (others can be granted permission to *use* it).
- **Attach** a service account to a workload (VM, Cloud Run, GKE through Workload Identity). The code then gets credentials from the metadata server automatically, through **Application Default Credentials (ADC)**. There are no keys in the code.
- **Avoid downloading JSON keys.** For things outside GCP (GitHub Actions, AWS, on-prem), use **Workload Identity Federation**.
- **Default service accounts** (like `PROJECT_NUMBER-compute@developer.gserviceaccount.com`) historically got the Editor role. **Create a dedicated service account per workload** with minimal roles.
- **Impersonation:** a human with `roles/iam.serviceAccountTokenCreator` on a service account can act as it (`--impersonate-service-account`). This is good for testing least privilege.
- **Service agents** (`service-PROJECT_NUMBER@gcp-sa-*.iam.gserviceaccount.com`) are Google-managed identities that GCP services use to act in your project. You'll grant one a role on Day 3.

### 1.4 Billing and cost

- A **billing account** pays. **Projects link to** a billing account (many-to-one). Unlink it and paid resources stop.
- **Budgets and alerts** *notify* you; **they don't cap spend.** (A hard cap means wiring the budget's Pub/Sub notification to automation that disables billing.)
- **Labels** (`env=prod`, `team=data`) and **billing export to BigQuery** are how real organizations allocate cost.
- Discounts: **sustained use** (automatic on some VM families), **committed use** (1 or 3 years, big savings), **Spot VMs** (up to about 90% off, can be preempted).
- **Free tier** includes, among others, an e2-micro VM in some US regions, 2M Cloud Run requests a month, 1 TB of BigQuery queries a month, and some Firestore and Pub/Sub usage.

### 1.5 Location

- **Region** = geographic area (for example `europe-west2`, London). **Zone** = one failure domain inside it (`europe-west2-a`).
- Choose a region based on: **latency to users → data residency or compliance → service availability → price**.
- Zonal resources die with their zone. **For high availability, spread across zones. For disaster recovery, spread across regions.** (Learn the scope table in the one-pager.)

### 1.6 How you interact with GCP

All of these call the **same REST APIs**:
- **Console** (UI): good for exploring and seeing what exists.
- **`gcloud` CLI** (+ `bq` for BigQuery, `kubectl` for GKE): good for repeatable actions. See [gcloud-patterns.md](cheatsheets/gcloud-patterns.md).
- **Client libraries:** your code.
- **Terraform:** infrastructure as code (Day 5).

**APIs are off by default per project.** "API not enabled" is the error you'll hit most often. Fix it with `gcloud services enable X.googleapis.com`.

---

## Lab (80 min)

Run these in **Cloud Shell**. Type them rather than pasting where you can, and read each output.

### Core

```bash
# 0. Variables (re-run this block at the start of EVERY day)
export PROJECT_ID="gcpweek-$(whoami | tr -dc 'a-z0-9' | head -c 8)-$RANDOM"   # must be globally unique
export REGION="us-central1"     # change if you prefer, but keep it one of the free-tier regions for the VM on Day 2
export ZONE="${REGION}-a"
printf 'export PROJECT_ID=%s REGION=%s ZONE=%s\n' "$PROJECT_ID" "$REGION" "$ZONE" > ~/gcpweek.env
#   On later days, start with:  source ~/gcpweek.env && gcloud config set project "$PROJECT_ID"

# 1. Create the project (labels = cost allocation tags) and make it the default
gcloud projects create "$PROJECT_ID" --name="GCP Week" --labels=purpose=learning,owner=me
gcloud config set project "$PROJECT_ID"
gcloud config set compute/region "$REGION"
gcloud config set compute/zone "$ZONE"
gcloud config list                       # what is gcloud pointing at right now?

# 2. Link billing
gcloud billing accounts list             # copy the ACCOUNT_ID
export BILLING_ACCOUNT="XXXXXX-XXXXXX-XXXXXX"
gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT"

# 3. Budget alert. Notifies at 50%, 90%, and when forecast to hit 100%
gcloud services enable billingbudgets.googleapis.com
gcloud billing budgets create \
  --billing-account="$BILLING_ACCOUNT" \
  --display-name="gcp-week" \
  --budget-amount=10 \
  --filter-projects="projects/$PROJECT_ID" \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.9 \
  --threshold-rule=percent=1.0,basis=forecasted-spend
#   (If this errors on permissions, do it in Console: Billing → Budgets & alerts. Same result.)

# 4. APIs are off by default. See what's on, then enable what this week needs
gcloud services list --enabled
gcloud services enable compute.googleapis.com run.googleapis.com \
  artifactregistry.googleapis.com cloudbuild.googleapis.com \
  iam.googleapis.com cloudresourcemanager.googleapis.com

# 5. Look at IAM: who has what on this project right now?
gcloud projects get-iam-policy "$PROJECT_ID" \
  --flatten="bindings[].members" --format="table(bindings.role, bindings.members)"
#   Question: why are you Owner? (You created it.) Which service accounts appeared after enabling APIs? (Service agents)

# 6. Roles are bundles of permissions. Compare a narrow and a broad role
gcloud iam roles describe roles/storage.objectViewer
gcloud iam roles describe roles/editor --format="value(includedPermissions)" | tr ';' '\n' | wc -l
#   objectViewer has a handful of permissions; editor has thousands. That's why "Editor everywhere" is dangerous.

# 7. Create a dedicated service account for this week's app (used from Day 2)
gcloud iam service-accounts create notes-api-sa --display-name="notes-api runtime"
export APP_SA="notes-api-sa@${PROJECT_ID}.iam.gserviceaccount.com"
echo "export APP_SA=$APP_SA BILLING_ACCOUNT=$BILLING_ACCOUNT" >> ~/gcpweek.env
gcloud iam service-accounts list
#   Note: we give it NO roles yet. Day 3 adds exactly the ones it needs, on exactly the resources it needs.
```

### Stretch

```bash
# Prove least privilege with impersonation: act as the service account and see what it CAN'T do
gcloud iam service-accounts add-iam-policy-binding "$APP_SA" \
  --member="user:$(gcloud config get-value account)" --role="roles/iam.serviceAccountTokenCreator"
# (wait about 60s for IAM to propagate)
gcloud storage buckets list --impersonate-service-account="$APP_SA"   # expect PERMISSION_DENIED. Good
```

Then explore in the **Console**: IAM & Admin → IAM (tick "Include Google-provided role grants" to see service agents) → Roles → Service Accounts. Then Billing → Reports.

---

## Recall (25 min): blank page, no peeking

**Draw:** the hierarchy (org → folders → projects → resources). Mark where you'd attach (a) a "no public buckets" rule, (b) the data team's read access to all prod data, (c) a single service account's access to one bucket.

**Answer in writing:**
1. Name the 3 parts of an IAM binding.
2. Someone is Editor on a folder. You remove them from a project under it. What happens?
3. IAM vs Org Policy: one sentence each.
4. Why is a downloaded service account key bad, and what replaces it (for GCP workloads, and for external ones)?
5. Do budgets stop spending?
6. A VM is zonal. What does that mean for availability?
7. Project ID vs name vs number: which is immutable and globally unique?

<details><summary>Answers</summary>

1. Principal (who), role (set of permissions), resource (where it's attached).
2. Nothing changes. Inherited allow grants can't be removed lower down. You'd need to remove it at the folder, or use a deny policy.
3. IAM controls *who* can perform actions. Org Policy limits *what configurations* are allowed for everyone.
4. Keys are long-lived secrets that leak and are hard to rotate. Attach a service account (ADC, through the metadata server) for GCP workloads. Use Workload Identity Federation for external ones.
5. No. Budgets alert. Capping needs automation (Pub/Sub notification → function that disables billing).
6. If the zone fails, the VM fails. Use a regional MIG or multiple zones for high availability.
7. Project ID.
</details>

## Work tie-in (15 min, read-only)

- In your company's Console, open the project picker → **All**. Sketch the folder and project structure. How are environments separated?
- Open IAM on a project you use. Which roles are granted to groups and which to individuals? Can you spot `Editor` or `Owner` given to a service account?
- If you have permission: `gcloud asset search-all-resources --scope=projects/WORK_PROJECT_ID --format="table(assetType,name)" | head -50` lists everything in a project. It's the fastest way to understand an unfamiliar environment.

## Flashcards

The Day 1 cards are in `flashcards.csv` (tag `day1`). Add any fact that surprised you today.

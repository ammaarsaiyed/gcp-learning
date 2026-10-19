# GCP in 5 Days

A short, hands-on course on Google Cloud fundamentals, built for someone who learns on the job and has bounced off the 72-hour learning paths.

**Goal:** by Friday you can (1) explain the core GCP building blocks and when to use each, (2) deploy and wire up a real app with `gcloud`, and (3) look at any architecture diagram, or a blank page, and name every part of the solution.

**What it costs you:** about 3 focused hours a day, so about 15 hours in total. If a day only has 90 minutes, do the **Core** parts and skip **Stretch**.

---

## Why the long courses didn't stick (and what this course does instead)

| What went wrong | Why | What we do here |
|---|---|---|
| 72 hours of video, little retained | Watching builds *recognition*, not *recall*. You feel like you know it, but you can't produce it. | Every day ends with **recall from a blank page**, a **diagram drawn from memory** and **flashcards**. |
| Each service taught on its own | Without a skeleton, 200 services are 200 unrelated facts. | You learn **one skeleton (the 8 lenses)** first. Every service is a slot in it. |
| Slow sub-modules | Courses pace for the slowest learner and pad for completeness. | Notes are compressed to what you need for design and daily work. Labs are copy-paste and build on each other. |
| Labs are throwaway | Each lab sets up a new toy, so nothing builds up. | **One app grows all week**: Cloud Run → Firestore → Pub/Sub → BigQuery → Secret Manager → private network. |
| Learning is separate from work | Nothing to hook the knowledge onto. | Each day has a **"Work tie-in"** step: find the same thing in your company's GCP. |

### What tends to work for people (and has nothing to do with GCP)

I don't have personal anecdotes to give you. These are the patterns that come up again and again from engineers who got through the same "I've started this 5 times" loop:

1. **Build one real thing end to end.** Forrest Brazeal's *Cloud Resume Challenge* (cloudresumechallenge.dev, which has a GCP edition) became popular because people reported learning more from one connected project than from months of courses. This week's lab app uses the same idea.
2. **Breadth first, then depth on demand.** Most real systems use about 20 services. Learn the map and the decision rules. Go deep only when work needs it.
3. **Translate from what you know.** If you know any other cloud (or just Linux and networking), map the new idea onto the old one. There is an AWS/Azure → GCP table in [00-gcp-on-one-page.md](00-gcp-on-one-page.md).
4. **Use the syllabus, not the course.** The ACE exam guide is a good *checklist* of what matters. The 72-hour path is one (slow) way of covering it. You don't need the path to use the checklist.
5. **Explain it to someone.** If you can't explain it in two sentences, you don't know it yet (the Feynman technique). Your recall sheet each day is exactly this.
6. **Spaced repetition beats re-reading.** 10 minutes of flashcards on days 1, 3, 7, 14 and 30 after the week does more than re-watching a course.

---

## The week

| Day | Topic | You will be able to… | Lab output |
|---|---|---|---|
| [1](day-1-foundations.md) | **Foundations:** resource hierarchy, IAM, billing, regions, `gcloud` | Explain *who can do what, where, and who pays* | Project, budget alert, service account with least privilege |
| [2](day-2-compute.md) | **Compute and deploy:** GCE, MIGs, GKE, Cloud Run, functions, CI/CD | Pick the right place to run code and deploy to it | VM with nginx, Cloud Run API with a canary rollout |
| [3](day-3-data.md) | **Data and integration:** Cloud Storage, databases, BigQuery, Pub/Sub, events | Pick the right store and decouple with messaging | API writes to Firestore, events flow through Pub/Sub into BigQuery |
| [4](day-4-network-security-ops.md) | **Network, security, operations:** VPC, LB, NAT, IAP, secrets, logging | Secure and connect things, see what's happening | Private VM over IAP + Cloud NAT, secret injected into Cloud Run, logs queried |
| [5](day-5-architecture.md) | **Architecture:** patterns, Well-Architected, design drills | Design a solution and break down an existing one | 6 design drills, your own reference diagram, teardown |

Keep these open all week:

- [00-gcp-on-one-page.md](00-gcp-on-one-page.md): **the whole platform on one page.** Read it first, then re-read it every morning (5 minutes).
- [cheatsheets/decision-trees.md](cheatsheets/decision-trees.md): which compute, storage, database, load balancer, connectivity or messaging service to pick.
- [cheatsheets/solution-design-template.md](cheatsheets/solution-design-template.md): the checklist for designing or breaking down any solution.
- [cheatsheets/gcloud-patterns.md](cheatsheets/gcloud-patterns.md): the CLI grammar, so you can guess commands instead of memorizing them.
- [flashcards.csv](flashcards.csv): import into Anki (or any SRS app) on Day 1 and add to it each day.
- [lab/app/](lab/app/): the app you deploy and extend all week.

## The daily loop (about 3 hours)

```
 0:00  Warm-up      (10m)  Re-read 00-gcp-on-one-page.md and do yesterday's flashcards
 0:10  Read         (40m)  Today's notes. Active reading: predict the answer before each "Why"
 0:50  Lab          (80m)  Type the commands; don't just paste them. Read every output
 2:10  Recall       (25m)  Close everything. On a blank page: today's diagram + the recall questions
 2:35  Work tie-in  (15m)  Find today's concepts in your company's GCP (read-only)
 2:50  Log          (10m)  Write 5 bullets in a learning log: what surprised you, what's still fuzzy
```

The recall step is the one that makes it stick. Don't skip it, and don't look at the answers until you've written yours.

## Setup (15 minutes, before Day 1)

1. **Use a personal Google account and a fresh project**, not your work organization. Corporate org policies often block things like public Cloud Run URLs. New accounts get a free trial credit (see cloud.google.com/free). This whole week should cost a few dollars at most if you run the teardown.
2. **Use Cloud Shell** (the `>_` icon at the top of the Console). It has `gcloud`, `bq`, `kubectl`, `git`, Docker and an editor already installed and authenticated. Nothing to install.
3. In Cloud Shell, clone this repo: `git clone <this repo's URL> && cd gcp-learning`.
4. Import `flashcards.csv` into Anki (File → Import). The header lines set up the Front/Back/Tags columns and the day tags (`day1`…`day5`). After each day's lesson, study that day's cards (Browse → filter `tag:day1` and so on).

## After the week

- **Days 6–30:** 10 minutes of flashcards a day. Re-read the one-pager weekly.
- **Each work task:** before you start, sketch which of the 8 lenses it touches.
- **Going deeper:** read the Architecture Center reference architecture for whatever you're building, then come back to the ACE exam guide and tick off what you can now do. You'll find most of it is already covered.

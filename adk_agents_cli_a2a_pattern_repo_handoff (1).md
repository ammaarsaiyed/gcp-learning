# Google ADK `agents-cli` A2A Integration in a Multi-Pattern Template Repository

## Purpose

This document is a technical handoff for an engineer or coding agent reviewing a private ADK repository that has already been upgraded with `agents-cli scaffold upgrade`.

The repository is **not a conventional single-agent project**. It is a **pattern/template catalogue** containing roughly fourteen top-level agent-pattern directories (for example HITL, sequential, hierarchical, etc.). Some patterns themselves contain multiple internal agents. A developer may:

1. clone the repository and run/test all patterns as a catalogue, or
2. select one pattern and delete the rest to use the repository as a project starter.

The repository already has its own application/server entrypoint and runtime conventions. The goal is therefore **not** to blindly replace the existing architecture with the generated scaffold, but to understand what `agents-cli` added and integrate the useful parts correctly.

---

## What `agents-cli scaffold upgrade` added and why

Recent `agents-cli` scaffolds generate runtime infrastructure such as:

```text
fast_api_app.py
app_utils/
  a2a.py
  services.py
```

These files are best understood as **generated serving/deployment infrastructure**, not application-domain code.

In particular, the generated A2A helper exists because current `agents-cli` serving architecture exposes an ADK application through multiple interfaces from the same process. A typical generated deployment surface provides:

```text
ADK App / root agent
        │
        ├── ADK API / Dev UI
        ├── A2A
        └── deployment/runtime-specific integration
```

The generated `app_utils/a2a.py` is therefore a **protocol adapter**. It takes an existing ADK agent and Runner, builds the A2A-facing metadata and request handling around them, and mounts the required HTTP/A2A routes into an existing FastAPI application.

It is not where agent behaviour should live.

The important consequence is:

> A2A is not something the developer must manually reimplement. The generated helper can wrap an existing ADK agent and existing Runner.

---

## What `fast_api_app.py` should mean in this repository

Do **not** assume that the generated `fast_api_app.py` must replace the repository's existing server entrypoint.

For a normal `agents-cli` project, the generated file acts as the canonical deployment-facing FastAPI application. In this repository, however, there is already a custom server application and custom startup path, for example:

```text
main.py
  ↓
server_app.py
```

If `server_app.py` contains real repository-specific behaviour — middleware, routes, startup/shutdown logic, custom Runner configuration, authentication, observability, integrations, etc. — the better model is:

```text
Application-owned runtime
-------------------------
main.py
server_app.py
agent / pattern implementations

Generated infrastructure
------------------------
fast_api_app.py
app_utils/a2a.py
app_utils/services.py
```

The practical recommendation is:

- **keep `fast_api_app.py` intact as generated infrastructure / deployment reference**;
- **do not merge application-specific logic into it unless there is a strong reason**;
- integrate the generated A2A helper into the repository's own server architecture where appropriate;
- avoid creating two independent runtime implementations that drift semantically.

In other words, consolidate **runtime concepts**, not necessarily files.

A future `scaffold upgrade` can then continue updating Google's generated infrastructure without overwriting repository-specific server code.

---

## The A2A helper can use the repository's own Runner

The key generated primitive is conceptually:

```python
await attach_a2a_routes(
    fastapi_app,
    agent=root_agent,
    runner=runner,
    task_store=...,
    rpc_path="/a2a/<name>",
)
```

The important input is `runner`.

The helper does not require a special `agents-cli` Runner. It is designed to expose the supplied ADK agent through A2A using the supplied Runner.

Therefore, if the private repository already creates a Runner with custom configuration, the preferred integration may be:

```text
existing server app
      │
      ├── existing application routes
      ├── existing middleware
      ├── existing Runner(s)
      └── generated attach_a2a_routes(...)
```

rather than creating an unrelated second execution stack only for A2A.

The local implementation must still be reviewed carefully for lifecycle compatibility, shared services, plugin configuration, state handling, and Runner ownership.

---

## Avoid accidental state separation

A subtle failure mode is to run the same apparent agent through multiple independent state backends:

```text
Dev UI
  ↓
Runner A
  ↓
SessionService A

A2A
  ↓
Runner B
  ↓
SessionService B
```

This produces two interfaces that appear to target the same agent but do not share sessions/artifacts/state.

The generated scaffold's `services.py` exists largely to centralize stateful services so different serving interfaces can share the same process-wide dependencies.

A healthier conceptual model is:

```text
                    shared services
             ┌────────────────────────┐
             │ SessionService         │
             │ ArtifactService        │
             │ MemoryService, if used │
             └───────────┬────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
          ADK API/UI               A2A
              │                     │
          Runner(s)             Runner(s)
              │                     │
              └──── same App/state boundary
```

It is not mandatory that every interface use the exact same Runner object, but they should not unintentionally create disconnected state systems for the same logical ADK application.

If the repository already has carefully managed services, prefer adapting the generated A2A wiring to those rather than introducing a parallel state stack.

---

# The multi-pattern repository changes the architecture

## Dev UI discovery and A2A exposure are different things

The repository contains many top-level pattern directories, for example:

```text
app/
  agents/
    sequential/
    hierarchical/
    hitl/
    parallel/
    ...
```

ADK's development tooling can treat these directories as separate loadable applications/patterns for the Dev UI.

However:

> **Being visible in the ADK Dev UI does not automatically expose a pattern over A2A.**

The stock generated `fast_api_app.py` is fundamentally scaffolded around **one ADK application**. It imports one app/root agent, creates one Runner, and mounts one A2A route.

Conceptually:

```python
await attach_a2a_routes(
    app,
    agent=root_agent,
    runner=runner,
    rpc_path=f"/a2a/{adk_app.name}",
)
```

That exposes one application.

For a pattern catalogue, the repository must deliberately decide which patterns to expose over A2A.

---

## Recommended A2A boundary: one top-level pattern = one A2A application

For this repository, the clean default is:

```text
ADK Dev UI
  ├── sequential
  ├── hierarchical
  ├── hitl
  └── ...

A2A
  ├── /a2a/sequential
  ├── /a2a/hierarchical
  ├── /a2a/hitl
  └── ...
```

Each top-level pattern should normally expose **its root application/root agent**, not every internal agent recursively.

For example:

```text
agents/
  hierarchical/
    agent.py
    agents/
      manager.py
      researcher.py
      writer.py
```

The default external A2A boundary should be:

```text
/a2a/hierarchical
```

not:

```text
/a2a/hierarchical/manager
/a2a/hierarchical/researcher
/a2a/hierarchical/writer
```

The internal manager/researcher/writer topology is part of the hierarchical pattern's implementation.

This preserves an important conceptual distinction:

```text
ADK in-process multi-agent composition
                  ≠
A2A service boundary
```

Only expose internal agents individually when the pattern is intentionally teaching or demonstrating **independently addressable A2A services**.

---

## Multiple A2A applications can share one FastAPI process

The generated A2A helper is suitable for a catalogue model because it can be attached once per application, provided each attachment has its own app/agent/Runner/path.

Conceptually:

```python
for pattern in patterns:
    await attach_a2a_routes(
        fastapi_app,
        agent=pattern.root_agent,
        runner=pattern.runner,
        task_store=pattern.task_store,
        rpc_path=f"/a2a/{pattern.name}",
    )
```

Result:

```text
one FastAPI process
    │
    ├── /a2a/sequential
    ├── /a2a/hierarchical
    ├── /a2a/hitl
    └── ...
```

This is especially useful for the catalogue mode because every pattern can be demonstrated locally without needing fourteen separate processes.

Architecturally, however, each route should still be treated as the external interface of a separate logical ADK application.

---

# Runner model for a pattern catalogue

## Do not use one Runner for all patterns

A Runner should be considered tied to a particular ADK application/runtime boundary.

For fourteen top-level pattern applications, the preferred shape is:

```text
                    shared infrastructure
              ┌───────────────────────────┐
              │ session service           │
              │ artifact service          │
              │ memory service, if used   │
              └─────────────┬─────────────┘
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
 sequential Runner    HITL Runner    hierarchical Runner
          │                 │                  │
 sequential App        HITL App       hierarchical App
          │                 │                  │
 /a2a/sequential      /a2a/hitl      /a2a/hierarchical
```

Each pattern can have its own Runner while sharing suitable infrastructure beneath it.

This matches the conceptual role of the Runner better than attempting to route many unrelated applications through one Runner.

The implementation agent should inspect the repository's existing Runner creation and determine:

- whether a Runner already exists per pattern;
- whether the Dev UI creates Runners internally;
- which stateful services are shared;
- whether custom plugins/middleware/hooks are attached at Runner creation;
- whether A2A should reuse an existing Runner or create an equivalent Runner using the same shared services.

---

# Suggested repository architecture

A good target shape is approximately:

```text
app/
  agents/
    sequential/
    hierarchical/
    hitl/
    ...
  app_utils/
    a2a.py            # generated helper
    services.py       # generated/shared services
  server_app.py       # repository-owned catalogue-aware server
  fast_api_app.py     # generated agents-cli serving/deployment reference

main.py               # repository-owned entrypoint
```

Responsibilities:

### `main.py`
Starts the repository's normal application/runtime.

### `server_app.py`
Owns the real application composition:
- FastAPI application construction;
- middleware;
- repository-specific routes;
- startup/shutdown;
- pattern discovery/registration;
- Runner lifecycle;
- mounting A2A routes for selected patterns;
- preserving the existing Dev UI behaviour.

### `fast_api_app.py`
Keep as generated infrastructure unless there is a deliberate decision to adopt it as the canonical server. It is useful as:
- a reference implementation of the current `agents-cli` expectations;
- a deployment-compatible surface;
- a comparison point when upgrading scaffold versions.

### `app_utils/a2a.py`
Treat as generated protocol plumbing. Prefer consuming it rather than copying/reimplementing A2A server internals.

### `app_utils/services.py`
Treat as generated/shared runtime-service plumbing unless the repository already has equivalent abstractions. Reconcile it with existing services rather than blindly creating duplicate state backends.

---

# Catalogue mode vs template mode

A major advantage of this architecture is that the same runtime can support both intended repository use cases.

## Catalogue mode

A developer clones the repository without deleting patterns.

Running the normal server can expose:

```text
Dev UI
  sequential
  hierarchical
  hitl
  parallel
  ...

A2A
  /a2a/sequential
  /a2a/hierarchical
  /a2a/hitl
  /a2a/parallel
  ...
```

This allows developers to inspect and interactively test each pattern.

## Template mode

A developer selects `hierarchical` and removes the rest.

The exact same server architecture now naturally exposes only:

```text
Dev UI
  hierarchical

A2A
  /a2a/hierarchical
```

This is desirable because the catalogue architecture collapses cleanly into the single-pattern project architecture rather than requiring a different server implementation.

---

# Pattern discovery

There are two broad choices.

## 1. Explicit registry

Example:

```python
PATTERNS = {
    "sequential": ...,
    "hierarchical": ...,
    "hitl": ...,
}
```

Advantages:
- explicit;
- easy to understand;
- deterministic;
- allows per-pattern metadata/configuration;
- avoids accidentally loading helper directories or invalid modules.

For a reference/template repository this is often the safest design.

## 2. Filesystem/ADK-loader discovery

If the repository's directory conventions are strict and already compatible with ADK's loader, the server could enumerate available patterns and load each one dynamically.

Advantages:
- deleting a pattern automatically removes it from both Dev UI and A2A exposure;
- less registry maintenance.

Risks:
- directory discovery can be permissive;
- helper/non-agent directories may be detected unless filtered;
- errors in one pattern may interfere with catalogue startup;
- pattern-specific configuration may become implicit.

A practical compromise is automated discovery plus explicit validation/filtering.

The implementation agent should inspect the real repository before choosing.

---

# How to test the generated A2A integration locally

## 1. Start the server that actually mounts A2A

Either run the generated application directly or, preferably once integrated, run the repository's normal server.

For a generated app this commonly looks conceptually like:

```bash
uv run uvicorn app.fast_api_app:app --reload --port 8000
```

For the private repository, preserve its existing startup command if that is the intended runtime.

---

## 2. Inspect each Agent Card

Each exposed A2A application should have a discoverable card beneath its A2A path.

Conceptually:

```text
/a2a/sequential/.well-known/agent-card.json
/a2a/hierarchical/.well-known/agent-card.json
/a2a/hitl/.well-known/agent-card.json
```

Test each card first.

This verifies:
- the route is mounted;
- the correct root agent is being described;
- the RPC URL is correct;
- capabilities/skills are being emitted;
- path collisions have not occurred.

---

## 3. Test with a real A2A consumer, not only `curl`

The most meaningful integration test is to create a minimal ADK consumer using a remote A2A agent and point it at one of the catalogue endpoints.

Conceptually:

```text
Consumer ADK Dev UI
        │
        ▼
consumer root agent
        │
        │ A2A
        ▼
/a2a/hierarchical
        │
        ▼
hierarchical root agent
        │
        ▼
its internal sub-agents
```

This proves more than HTTP reachability. It validates:
- Agent Card discovery;
- client/server protocol compatibility;
- request execution;
- streaming/events if used;
- response conversion;
- the actual ADK-to-A2A integration.

For the catalogue repository this can become a first-class demonstration pattern: one pattern may intentionally consume another pattern over A2A.

---

# A2A as a teaching pattern in this repository

The repository is well positioned to demonstrate the difference between in-process composition and protocol-level composition.

For example:

```text
In-process patterns
-------------------
SequentialAgent
ParallelAgent
hierarchical delegation
sub_agents
AgentTool

Cross-boundary composition
--------------------------
Remote A2A agent
Agent Card discovery
A2A request/response
independently addressable agent service
```

A dedicated A2A pattern could call another pattern:

```text
a2a_orchestrator
      │
      ├── A2A → /a2a/sequential
      └── A2A → /a2a/hierarchical
```

Even if all endpoints are hosted in one process during catalogue mode, the demonstration still models proper service boundaries.

---

# Do not reimplement the generated A2A plumbing unless necessary

Other repositories in the organisation may manually construct:
- Agent Cards;
- request handlers;
- executors;
- A2A protocol routing;
- compatibility behaviour;
- task stores;
- transport wiring.

Where practical, prefer the generated `attach_a2a_routes()` integration over duplicating these internals.

The main reasons are:
- less protocol boilerplate;
- less version-sensitive code;
- consistency across repositories;
- easier adoption of future `agents-cli`/ADK/A2A changes;
- cleaner separation between application logic and transport logic.

Application code should ideally own:
- root agent / ADK App;
- Runner semantics;
- services;
- domain behaviour;
- auth/policy requirements;
- server composition.

Generated infrastructure should own as much of the protocol translation as possible.

---

# Key decisions the on-machine agent should make after inspecting the private code

The implementation should **not** be applied mechanically. Review the actual server and answer these questions first:

1. **What exactly does `server_app.py` own today?**
   - FastAPI construction?
   - ADK Dev UI?
   - custom endpoints?
   - authentication?
   - lifespan logic?
   - observability?
   - environment/config setup?

2. **Where are Runners created today?**
   - one shared Runner?
   - one per pattern?
   - created by ADK tooling internally?
   - custom Runner subclasses/plugins?

3. **What stateful services already exist?**
   - session service;
   - artifact service;
   - memory service;
   - credential service;
   - persistence backend.

4. **Does the current Dev UI already support all pattern directories through one `agents_dir`?**

5. **What object does each pattern expose?**
   - `root_agent`;
   - `App`;
   - custom factory;
   - lazy loader.

6. **Can each top-level pattern be assigned a stable unique app name?**

7. **Should all patterns be A2A-enabled by default in catalogue mode, or should some be explicitly excluded?**

8. **Are there patterns whose internal agents intentionally need independent A2A service boundaries?**
   - if not, expose only the top-level root.

9. **Can `app_utils/services.py` be used directly, or must it be adapted to existing repository services?**

10. **Can the existing Runner be passed into `attach_a2a_routes()` safely?**
    - correct lifespan;
    - correct app binding;
    - correct shared services;
    - correct plugins/hooks.

11. **If a separate A2A Runner is created, does it share the same stateful services as the normal runtime?**

12. **Does `scaffold upgrade` need to remain safe in future?**
    - if yes, minimize edits to generated files;
    - put repository-specific integration in repository-owned modules.

---

# Recommended end state

The strongest default architecture for this repository is:

```text
                           server_app.py
                                │
                    repository-owned composition
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
        ADK Dev UI/API                       A2A registration
              │                                   │
      discovers/loads patterns             one attachment per
              │                             top-level pattern
              │                                   │
      ┌───────┼────────┐                  ┌───────┼────────┐
      │       │        │                  │       │        │
 sequential  HITL  hierarchical      /a2a/seq /a2a/hitl /a2a/hier
      │       │        │
    Runner  Runner   Runner
      │       │        │
      └───────┴────────┘
              │
        shared services
```

with:

```text
fast_api_app.py
```

kept as generated `agents-cli` infrastructure/reference rather than becoming the place where repository-specific logic accumulates.

The exact code should be adapted to the private implementation, but the conceptual rules should remain:

1. **one logical top-level pattern = one ADK application boundary;**
2. **one Runner per application is the clean default;**
3. **shared services are preferable to duplicated state backends;**
4. **A2A exposure must be mounted explicitly per application;**
5. **Dev UI discovery does not itself imply A2A exposure;**
6. **internal sub-agents stay internal unless the pattern intentionally models separate A2A services;**
7. **use the generated A2A helper instead of manually rebuilding protocol plumbing;**
8. **keep generated scaffold files upgradeable where possible;**
9. **make the repository-owned server catalogue-aware rather than forcing a single-agent scaffold to define the architecture;**
10. **verify the final design through both Agent Card inspection and an actual A2A consumer.**

This should give the private-code agent enough context to inspect the real implementation and decide where the generated `agents-cli` runtime pieces should be reused, adapted, or isolated without losing the repository's existing Dev UI and template-catalogue behaviour.

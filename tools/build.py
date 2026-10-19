#!/usr/bin/env python3
"""Build the practice app and flashcards from the markdown sources.

Sources (edit these, then re-run `python3 tools/build.py`):
  atlas/*.md                 concept atlas  (### Term / `tier` · Related: / **What:** ...)
  practice/architectures.md  architecture library
  practice/scenarios.md      scenario questions

Outputs:
  app/index.html   the interactive practice app (template + embedded JSON data)
  flashcards.csv   Anki-ready cards (concepts + the original week-1 cards)
"""
import csv
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = {"What": "what", "How": "how", "GCP": "gcp", "Watch out": "watch", "Why it matters": "why", "GCP use": "gcp2"}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def parse_atlas():
    domains, concepts = [], []
    for path in sorted(glob.glob(os.path.join(ROOT, "atlas", "[0-9][0-9]-*.md"))):
        text = open(path, encoding="utf-8").read()
        num = os.path.basename(path)[:2]
        title = re.search(r"^# \d+ · (.+)$", text, re.M).group(1).strip()
        intro = text.split("\n---", 1)[0].split("\n", 1)[1].strip()
        intro = re.sub(r"\*\*Tiers:\*\*.*", "", intro).strip()
        did = slug(os.path.basename(path)[3:-3])
        domains.append({"id": did, "num": num, "title": title, "intro": intro})
        for block in re.split(r"^### ", text, flags=re.M)[1:]:
            lines = block.strip().split("\n")
            term = lines[0].strip()
            meta = lines[1].strip() if len(lines) > 1 else ""
            m = re.match(r"`(core|working|aware)`(?:\s*·\s*Related:\s*(.*))?", meta)
            if not m:
                sys.exit(f"{path}: bad tier line for '{term}': {meta!r}")
            c = {"id": f"{did}--{slug(term)}", "domain": did, "term": term, "tier": m.group(1),
                 "related": [r.strip() for r in (m.group(2) or "").split(",") if r.strip()]}
            body = "\n".join(lines[2:])
            for label, key in FIELDS.items():
                fm = re.search(r"\*\*" + re.escape(label) + r":\*\*\s*(.+?)(?=\n\*\*[A-Z][\w ]*:\*\*|\Z)", body, re.S)
                if fm:
                    c[key] = fm.group(1).strip()
            if "gcp2" in c:
                c["gcp"] = (c.get("gcp", "") + " " + c.pop("gcp2")).strip()
            if "what" not in c:
                sys.exit(f"{path}: '{term}' has no **What:**")
            concepts.append(c)
    return domains, concepts


def parse_architectures():
    text = open(os.path.join(ROOT, "practice", "architectures.md"), encoding="utf-8").read()
    archs = []
    for block in re.split(r"^## Arch: ", text, flags=re.M)[1:]:
        title, rest = block.split("\n", 1)
        get = lambda k: re.search(rf"^{k}:\s*(.+)$", rest, re.M).group(1).strip()
        nodes_txt = rest.split("\nnodes:\n", 1)[1].split("\nedges:\n", 1)[0]
        edges_txt = rest.split("\nedges:\n", 1)[1]
        nodes, edges = [], []
        for ln in nodes_txt.strip().split("\n"):
            parts = [p.strip() for p in ln.lstrip("- ").split("|")]
            nid, label, cat, pos = parts[:4]
            why = "|".join(parts[4:]).strip()
            col, row = (int(x) for x in pos.split(","))
            nodes.append({"id": nid, "label": label, "cat": cat, "col": col, "row": row, "why": why})
        ids = {n["id"] for n in nodes}
        for ln in edges_txt.strip().split("\n"):
            if not ln.strip().startswith("-"):
                continue
            m = re.match(r"-\s*(\S+)\s*>\s*(\S+)\s*\|\s*(.+)$", ln.strip())
            if not m:
                sys.exit(f"bad edge line in '{title}': {ln}")
            a, b, lab = m.groups()
            if a not in ids or b not in ids:
                sys.exit(f"edge {a}>{b} references unknown node in '{title}'")
            edges.append({"from": a, "to": b, "label": lab.strip()})
        seen = {}
        for n in nodes:
            k = (n["col"], n["row"])
            if k in seen:
                sys.exit(f"'{title}': nodes {seen[k]} and {n['id']} overlap at {k}")
            seen[k] = n["id"]
        archs.append({"id": get("id"), "title": title.strip(), "level": get("level"),
                      "context": get("context"), "nodes": nodes, "edges": edges})
    return archs


def parse_scenarios():
    text = open(os.path.join(ROOT, "practice", "scenarios.md"), encoding="utf-8").read()
    qs = []
    for i, block in enumerate(re.split(r"^### Q · ", text, flags=re.M)[1:]):
        lines = block.strip().split("\n")
        domain = lines[0].strip()
        q, opts, expl = [], [], []
        for ln in lines[1:]:
            if ln.startswith("- ["):
                opts.append({"text": ln[6:].strip(), "correct": ln[3] == "x"})
            elif ln.startswith(">"):
                expl.append(ln[1:].strip())
            elif ln.strip() and not opts:
                q.append(ln.strip())
        if sum(o["correct"] for o in opts) != 1:
            sys.exit(f"scenario {i + 1} ({domain}) must have exactly one correct option")
        qs.append({"id": f"q{i + 1}", "domain": domain, "q": " ".join(q), "options": opts, "explain": " ".join(expl)})
    return qs


def _field(rest, key):
    m = re.search(rf"^{key}:\s*(.+)$", rest, re.M)
    return m.group(1).strip() if m else ""


def _section(rest, start, ends):
    if f"\n{start}:\n" not in "\n" + rest:
        return ""
    body = ("\n" + rest).split(f"\n{start}:\n", 1)[1]
    cut = len(body)
    for e in ends:
        i = body.find(f"\n{e}")
        if i != -1:
            cut = min(cut, i)
    return body[:cut]


def _nodes(txt, where):
    nodes = []
    for ln in txt.strip().split("\n"):
        if not ln.strip().startswith("-"):
            continue
        parts = [p.strip() for p in ln.strip()[1:].split("|")]
        if len(parts) < 4:
            sys.exit(f"{where}: bad node line {ln!r}")
        col, row = (int(x) for x in parts[3].split(","))
        nodes.append({"id": parts[0], "label": parts[1], "cat": parts[2], "col": col, "row": row,
                      "why": "|".join(parts[4:]).strip()})
    seen = {}
    for n in nodes:
        k = (n["col"], n["row"])
        if k in seen:
            sys.exit(f"{where}: nodes {seen[k]} and {n['id']} overlap at {k}")
        seen[k] = n["id"]
    return nodes


def _edges(txt, ids, where):
    edges = []
    for ln in txt.strip().split("\n"):
        if not ln.strip().startswith("-"):
            continue
        m = re.match(r"-\s*(\S+)\s*>\s*(\S+)\s*\|\s*(.+)$", ln.strip())
        if not m or m.group(1) not in ids or m.group(2) not in ids:
            sys.exit(f"{where}: bad edge {ln!r}")
        edges.append({"from": m.group(1), "to": m.group(2), "label": m.group(3).strip()})
    return edges


def parse_journeys(archs):
    text = open(os.path.join(ROOT, "guide", "02-end-to-end-journeys.md"), encoding="utf-8").read()
    amap = {a["id"]: a for a in archs}
    out = []
    for block in re.split(r"^## Journey: ", text, flags=re.M)[1:]:
        title, rest = block.split("\n", 1)
        arch = _field(rest, "arch")
        if arch not in amap:
            sys.exit(f"journey '{title}': unknown arch {arch}")
        ids = {n["id"] for n in amap[arch]["nodes"]}
        steps = []
        for ln in _section(rest, "steps", ["## "]).strip().split("\n"):
            if not ln.startswith("- "):
                continue
            nodes_s, txt = ln[2:].split("|", 1)
            hl = [x.strip() for x in nodes_s.split(",") if x.strip()]
            bad = [x for x in hl if x not in ids]
            if bad:
                sys.exit(f"journey '{title}': unknown nodes {bad}")
            steps.append({"nodes": hl, "text": txt.strip()})
        out.append({"id": _field(rest, "id"), "title": title.strip(), "arch": arch,
                    "lesson": _field(rest, "lesson"), "steps": steps})
    return out


def parse_labs():
    text = open(os.path.join(ROOT, "practice", "design-lab.md"), encoding="utf-8").read()
    labs = []
    for block in re.split(r"^## Lab: ", text, flags=re.M)[1:]:
        title, rest = block.split("\n", 1)
        where = f"lab '{title.strip()}'"
        reqs = [l[2:].strip() for l in _section(rest, "requirements", ["slots:"]).split("\n") if l.startswith("- ")]
        slots = _nodes(_section(rest, "slots", ["edges:"]), where)
        ids = {n["id"] for n in slots}
        edges = _edges(_section(rest, "edges", ["steps:"]), ids, where)
        steps = []
        for sb in re.split(r"^### ", rest.split("\nsteps:\n", 1)[1], flags=re.M)[1:]:
            head, body = sb.split("\n", 1)
            m = re.match(r"(Step|Twist): (.+?)\s*\|\s*slot:\s*(\S+)", head)
            if not m or m.group(3) not in ids:
                sys.exit(f"{where}: bad step header {head!r}")
            opts = []
            for ln in body.split("\n"):
                om = re.match(r"- (best|ok|poor) \| (.+?) \| (.+)$", ln.strip())
                if om:
                    opts.append({"grade": om.group(1), "label": om.group(2).strip(), "feedback": om.group(3).strip()})
            if not any(o["grade"] == "best" for o in opts):
                sys.exit(f"{where}: step {head!r} has no best option")
            steps.append({"kind": m.group(1).lower(), "title": m.group(2).strip(), "slot": m.group(3),
                          "question": _field(body, "question"), "options": opts})
        labs.append({"id": _field(rest, "id"), "title": title.strip(), "brief": _field(rest, "brief"),
                     "requirements": reqs, "slots": slots, "edges": edges, "steps": steps})
    return labs


def parse_reviews():
    text = open(os.path.join(ROOT, "practice", "design-reviews.md"), encoding="utf-8").read()
    revs = []
    for block in re.split(r"^## Review: ", text, flags=re.M)[1:]:
        title, rest = block.split("\n", 1)
        where = f"review '{title.strip()}'"
        nodes = _nodes(_section(rest, "nodes", ["edges:"]), where)
        edges = _edges(_section(rest, "edges", ["issues:"]), {n["id"] for n in nodes}, where)
        issues = []
        for ln in _section(rest, "issues", ["## "]).split("\n"):
            im = re.match(r"- \[( |x)\] (.+?) \| (.+)$", ln.strip())
            if im:
                issues.append({"real": im.group(1) == "x", "text": im.group(2).strip(), "explain": im.group(3).strip()})
        revs.append({"id": _field(rest, "id"), "title": title.strip(), "design": _field(rest, "design"),
                     "nodes": nodes, "edges": edges, "issues": issues})
    return revs


def read_guides():
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "guide", "0[134]-*.md"))):
        md = open(path, encoding="utf-8").read()
        title = re.search(r"^# (.+)$", md, re.M).group(1).strip()
        out.append({"id": os.path.basename(path)[:2], "title": title, "md": md})
    return out


def strip_md(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    return re.sub(r"`(.+?)`", r"\1", s)


def write_flashcards(concepts):
    out = os.path.join(ROOT, "flashcards.csv")
    week = []
    week_src = os.path.join(ROOT, "practice", "week1-cards.csv")
    if os.path.exists(week_src):
        with open(week_src, encoding="utf-8") as f:
            week = [r for r in csv.reader(l for l in f if not l.startswith("#"))]
    with open(out, "w", newline="", encoding="utf-8") as f:
        f.write("#separator:Comma\n#html:true\n#columns:Front,Back,Tags\n#tags column:3\n")
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        for c in concepts:
            back = "<b>What:</b> " + strip_md(c["what"])
            if c.get("how"):
                back += "<br><br><b>How:</b> " + strip_md(c["how"])
            if c.get("gcp"):
                back += "<br><br><b>GCP:</b> " + strip_md(c["gcp"])
            w.writerow([f"Explain: {c['term']}", back, f"atlas::{c['domain']} tier::{c['tier']}"])
        for r in week:
            w.writerow([r[0], r[1], "week1::" + r[2]])
    return len(concepts) + len(week)


def gh_anchor(term):
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", term.lower()))


def write_atlas_index(domains, concepts):
    lines = ["# Concept atlas: index", "",
             f"{len(concepts)} concepts in {len(domains)} domains. Generated by `tools/build.py`, so don't edit this file by hand.", "",
             "Tiers: **core** = explain it and design with it · *working* = explain it · aware = know what it is.", ""]
    for d in domains:
        cs = [c for c in concepts if c["domain"] == d["id"]]
        fname = f"{d['num']}-{d['id']}.md"
        lines += [f"## [{d['num']} · {d['title']}]({fname})", ""]
        fmt = {"core": "**{}**", "working": "*{}*", "aware": "{}"}
        lines.append(" · ".join(f"[{fmt[c['tier']].format(c['term'])}]({fname}#{gh_anchor(c['term'])})" for c in cs))
        lines.append("")
    open(os.path.join(ROOT, "atlas", "README.md"), "w", encoding="utf-8").write("\n".join(lines))


def main():
    domains, concepts = parse_atlas()
    write_atlas_index(domains, concepts)
    archs = parse_architectures()
    qs = parse_scenarios()
    journeys, labs, reviews, guides = parse_journeys(archs), parse_labs(), parse_reviews(), read_guides()
    data = {"domains": domains, "concepts": concepts, "architectures": archs, "scenarios": qs,
            "journeys": journeys, "labs": labs, "reviews": reviews, "guides": guides}
    tpl = open(os.path.join(ROOT, "app", "template.html"), encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = tpl.replace("/*__DATA__*/null", payload)
    open(os.path.join(ROOT, "app", "index.html"), "w", encoding="utf-8").write(html)
    n_cards = write_flashcards(concepts)
    tiers = {t: sum(c["tier"] == t for c in concepts) for t in ("core", "working", "aware")}
    print(f"{len(domains)} domains, {len(concepts)} concepts {tiers}, {len(archs)} architectures, "
          f"{len(qs)} scenarios, {n_cards} flashcards, {len(journeys)} journeys, {len(labs)} labs "
          f"({sum(len(l['steps']) for l in labs)} decisions), {len(reviews)} reviews, {len(guides)} guides")


if __name__ == "__main__":
    main()

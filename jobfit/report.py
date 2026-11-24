"""Render a JobFit result as Markdown."""

ICON = {"matched": "✅", "listed": "🟡", "missing": "❌"}


def to_markdown(r: dict) -> str:
    job, s, a = r["job"], r["score"], r.get("analysis", {})
    out = [f"# JobFit report: {job['title']}", ""]
    out.append(f"**Fit score: {s['total']}/100**" + (f" · verdict: **{a['verdict']}**" if a.get("verdict") else ""))
    out.append("")
    out.append(f"Must-have coverage {s['must']:.0%} · nice-to-have {s['nice']:.0%} · experience {s['years']:.0%}")
    if a.get("summary"):
        out += ["", a["summary"]]

    out += ["", "## Requirements", "", "| | Skill | Type | Evidence from resume |", "|---|---|---|---|"]
    for q in sorted(r["requirements"], key=lambda q: (q["kind"], ["missing", "listed", "matched"].index(q["status"]))):
        ev = (q["evidence"] or "").replace("|", "/")
        ev = ev[:110] + "…" if len(ev) > 110 else ev
        kind = "must" if q["kind"] == "must_have" else "nice"
        hint = " *(only listed; add a bullet showing you used it)*" if q["status"] == "listed" else ""
        out.append(f"| {ICON[q['status']]} | {q['skill']} | {kind} | {ev or '—'}{hint} |")

    for title, key in (("Strengths", "strengths"), ("Gaps", "gaps")):
        if a.get(key):
            out += ["", f"## {title}", ""] + [f"- {x}" for x in a[key]]

    sug = r.get("suggestions", {})
    if sug.get("rewrites"):
        out += ["", "## Suggested bullet rewrites", "",
                "Each rewrite only rephrases your existing bullet. Rewrites that added tools or numbers were removed.",
                ""]
        for rw in sug["rewrites"]:
            out += [f"- **Before:** {rw['original']}", f"  **After:** {rw['improved']}"]
    if sug.get("learn"):
        out += ["", "## How to close the gaps", ""] + [f"- **{x.get('skill', '')}:** {x.get('how', '')}"
                                                        for x in sug["learn"]]
    if r.get("rejected"):
        out += ["", f"<sub>{len(r['rejected'])} suggested rewrite(s) were blocked for adding unverified claims.</sub>"]
    return "\n".join(out) + "\n"

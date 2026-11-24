"""JobFit agent (LangGraph).

    START ─┬─► extract_jd ─────┐
           └─► extract_resume ─┴─► match ─► analyze ─► suggest ─► guard ─► END

- extract_*  run in parallel; the LLM structures the JD and resume
- match      deterministic: canonical skill matching, evidence lines, transparent score
- analyze    LLM hiring-manager view: strengths, gaps, verdict
- suggest    LLM rewrites existing bullets in the job's language and plans how to close gaps
- guard      rejects any rewrite that adds a skill or number the original bullet did not have
"""
import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from jobfit import prompts
from jobfit.llm import parse_json
from jobfit.parse import evidence_lines, years_required
from jobfit.skills import SKILLS, extract_skills, normalise

WEIGHTS = {"must": 0.60, "nice": 0.25, "years": 0.15}
LISTED_CREDIT = 0.6  # skill only appears in a skills list, with no bullet showing it was used


class FitState(TypedDict, total=False):
    resume: str
    jd: str
    job: dict
    profile: dict
    requirements: list[dict]
    score: dict
    analysis: dict
    suggestions: dict
    rejected: list[dict]


def _aliases(skill: str) -> list[str]:
    return [skill.lower()] + SKILLS.get(skill, [])


def _mentions(text: str, skill: str) -> bool:
    t = text.lower()
    return any(re.search(r"(?<![a-z0-9+#])" + re.escape(a) + r"(?![a-z0-9+#])", t) for a in _aliases(skill))


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def build_graph(llm):
    def ask(prompt):
        return llm.invoke(prompt).content

    def extract_jd(state: FitState):
        job = parse_json(ask(prompts.EXTRACT_JD.format(jd=state["jd"][:8000])), {})
        must = normalise(job.get("must_have", []))
        nice = normalise(job.get("nice_to_have", [])) - must
        if not must:  # LLM failed: fall back to the vocabulary scan
            must = extract_skills(state["jd"])
        return {"job": {"title": job.get("title") or "this role", "must_have": sorted(must),
                        "nice_to_have": sorted(nice), "responsibilities": job.get("responsibilities", [])[:6],
                        "years_required": years_required(state["jd"])}}

    def extract_resume(state: FitState):
        info = parse_json(ask(prompts.EXTRACT_RESUME.format(resume=state["resume"][:8000])), {})
        claimed = normalise(info.get("skills", []))
        # Keep only LLM-claimed skills that literally appear in the resume, plus the vocabulary scan.
        skills = {s for s in claimed if _mentions(state["resume"], s)} | extract_skills(state["resume"])
        try:
            years = float(info.get("years_experience") or 0)
        except (TypeError, ValueError):
            years = 0.0
        return {"profile": {"name": info.get("name", ""), "years_experience": years, "skills": sorted(skills)}}

    def match(state: FitState):
        lines = evidence_lines(state["resume"])
        have = set(state["profile"]["skills"])
        reqs = []
        for kind in ("must_have", "nice_to_have"):
            for skill in state["job"][kind]:
                ev = next((ln for ln in lines if _mentions(ln, skill)), None)
                if skill in have and ev:
                    status = "matched"
                elif skill in have or _mentions(state["resume"], skill):
                    status = "listed"
                else:
                    status = "missing"
                reqs.append({"skill": skill, "kind": kind, "status": status, "evidence": ev})

        def coverage(kind):
            rs = [r for r in reqs if r["kind"] == kind]
            if not rs:
                return 1.0
            return sum(1.0 if r["status"] == "matched" else LISTED_CREDIT if r["status"] == "listed" else 0.0
                       for r in rs) / len(rs)

        need = state["job"]["years_required"]
        years_fit = 1.0 if not need else min(1.0, state["profile"]["years_experience"] / need)
        parts = {"must": coverage("must_have"), "nice": coverage("nice_to_have"), "years": years_fit}
        total = round(100 * sum(WEIGHTS[k] * v for k, v in parts.items()))
        return {"requirements": reqs, "score": {"total": total, **{k: round(v, 2) for k, v in parts.items()}}}

    def analyze(state: FitState):
        cov = "\n".join(f"- {r['skill']} ({r['kind'].replace('_', ' ')}): {r['status']}" for r in state["requirements"])
        out = parse_json(ask(prompts.ANALYZE.format(title=state["job"]["title"], coverage=cov,
                                                    resume=state["resume"][:6000])), {})
        return {"analysis": {"strengths": out.get("strengths", []), "gaps": out.get("gaps", []),
                             "verdict": out.get("verdict", ""), "summary": out.get("summary", "")}}

    def suggest(state: FitState):
        matched = [r["skill"] for r in state["requirements"] if r["status"] != "missing"]
        missing = [r["skill"] for r in state["requirements"] if r["status"] == "missing"]
        bullets = [ln for ln in evidence_lines(state["resume"]) if extract_skills(ln)][:10]
        out = parse_json(ask(prompts.SUGGEST.format(title=state["job"]["title"], matched=", ".join(matched) or "none",
                                                    missing=", ".join(missing) or "none",
                                                    bullets="\n".join(f"- {b}" for b in bullets))), {})
        return {"suggestions": {"rewrites": out.get("rewrites", []), "learn": out.get("learn", [])}}

    def guard(state: FitState):
        kept, rejected = [], []
        for rw in state["suggestions"]["rewrites"]:
            orig, new = rw.get("original", ""), rw.get("improved", "")
            if not orig or not new:
                continue
            added_skills = extract_skills(new) - extract_skills(orig)
            added_numbers = _numbers(new) - _numbers(orig)
            if added_skills or added_numbers:
                rejected.append({**rw, "reason": "adds " + ", ".join(sorted(added_skills | added_numbers))})
            else:
                kept.append(rw)
        return {"suggestions": {**state["suggestions"], "rewrites": kept}, "rejected": rejected}

    g = StateGraph(FitState)
    for name, fn in [("extract_jd", extract_jd), ("extract_resume", extract_resume), ("match", match),
                     ("analyze", analyze), ("suggest", suggest), ("guard", guard)]:
        g.add_node(name, fn)
    g.add_edge(START, "extract_jd")
    g.add_edge(START, "extract_resume")
    g.add_edge(["extract_jd", "extract_resume"], "match")
    g.add_edge("match", "analyze")
    g.add_edge("analyze", "suggest")
    g.add_edge("suggest", "guard")
    g.add_edge("guard", END)
    return g.compile()


def run(llm, resume: str, jd: str) -> dict:
    return build_graph(llm).invoke({"resume": resume, "jd": jd})

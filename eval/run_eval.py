"""Real-model run of JobFit on the sample resume and job descriptions.

    python eval/run_eval.py --repeats 3

For each (resume, job) pair it runs the full pipeline several times (LLM output varies) and records:
  score             deterministic fit score (same inputs -> same score)
  rewrites_proposed bullet rewrites the LLM suggested
  rewrites_blocked  rewrites the guard rejected because they added a skill, tool or number
                    that is not in the original bullet
  latency / calls / tokens per run
Writes eval/results.json, eval/blocked_examples.jsonl and one example report per job in examples/.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jobfit.config import Settings  # noqa: E402
from jobfit.graph import run  # noqa: E402
from jobfit.llm import get_llm  # noqa: E402
from jobfit.report import to_markdown  # noqa: E402


class CountingLLM:
    def __init__(self, llm):
        self.llm, self.calls, self.tokens = llm, 0, 0

    def invoke(self, prompt):
        out = self.llm.invoke(prompt)
        self.calls += 1
        usage = (getattr(out, "response_metadata", {}) or {}).get("token_usage", {}) or {}
        self.tokens += usage.get("total_tokens", 0)
        return out


def summarize(runs: list[dict]) -> dict:
    proposed = sum(r["rewrites_proposed"] for r in runs)
    blocked = sum(r["rewrites_blocked"] for r in runs)
    return {
        "runs": len(runs),
        "scores": sorted({r["score"] for r in runs}),
        "rewrites_proposed": proposed,
        "rewrites_blocked": blocked,
        "blocked_share": round(blocked / proposed, 3) if proposed else 0.0,
        "avg_latency_s": round(sum(r["latency_s"] for r in runs) / len(runs), 2),
        "llm_calls_per_run": round(sum(r["calls"] for r in runs) / len(runs), 2),
        "tokens_per_run": round(sum(r["tokens"] for r in runs) / len(runs)),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--resume", default="samples/resume_priya.md")
    p.add_argument("--jds", nargs="+", default=["samples/jd_genai_engineer.md", "samples/jd_cv_engineer.md"])
    p.add_argument("--repeats", type=int, default=3)
    a = p.parse_args()

    settings = Settings()
    resume = (ROOT / a.resume).read_text(encoding="utf-8")
    (ROOT / "examples").mkdir(exist_ok=True)
    results, blocked_rows = {}, []
    for jd_path in a.jds:
        jd = (ROOT / jd_path).read_text(encoding="utf-8")
        runs = []
        for i in range(a.repeats):
            llm = CountingLLM(get_llm(settings))
            t0 = time.perf_counter()
            out = run(llm, resume, jd)
            sug = out.get("suggestions", {})
            rej = out.get("rejected", [])
            runs.append({"score": out["score"]["total"], "rewrites_proposed": len(sug.get("rewrites", [])) + len(rej),
                         "rewrites_blocked": len(rej), "latency_s": round(time.perf_counter() - t0, 2),
                         "calls": llm.calls, "tokens": llm.tokens})
            blocked_rows += [{"jd": jd_path, "run": i, **r} for r in rej]
            if i == 0:
                name = Path(jd_path).stem.replace("jd_", "")
                (ROOT / "examples" / f"report_{name}.md").write_text(to_markdown(out), encoding="utf-8")
            print(f"{jd_path} run {i + 1}: score={runs[-1]['score']} proposed={runs[-1]['rewrites_proposed']} "
                  f"blocked={runs[-1]['rewrites_blocked']}")
        results[jd_path] = summarize(runs)

    meta = {"model": f"{settings.llm_provider}/{settings.llm_model}", "resume": a.resume, "repeats": a.repeats}
    (ROOT / "eval" / "results.json").write_text(json.dumps({"config": meta, "results": results}, indent=2))
    with open(ROOT / "eval" / "blocked_examples.jsonl", "w") as f:
        for r in blocked_rows:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({"config": meta, "results": results}, indent=2))


if __name__ == "__main__":
    main()

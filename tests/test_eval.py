import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))

from run_eval import summarize  # noqa: E402


def test_summarize_counts_blocked_share():
    runs = [{"score": 70, "rewrites_proposed": 4, "rewrites_blocked": 1, "latency_s": 2, "calls": 4, "tokens": 900},
            {"score": 70, "rewrites_proposed": 4, "rewrites_blocked": 3, "latency_s": 4, "calls": 4, "tokens": 1100}]
    s = summarize(runs)
    assert s["scores"] == [70] and s["blocked_share"] == 0.5
    assert s["avg_latency_s"] == 3 and s["tokens_per_run"] == 1000

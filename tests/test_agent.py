from conftest import ScriptedLLM

from jobfit.graph import run
from jobfit.report import to_markdown


def _req(result, skill):
    return next(r for r in result["requirements"] if r["skill"] == skill)


def test_scores_with_evidence(resume, jd):
    r = run(ScriptedLLM(), resume, jd)
    assert _req(r, "RAG")["status"] == "matched"
    assert "RAG pipeline" in _req(r, "RAG")["evidence"]
    assert _req(r, "Vector Databases")["status"] == "matched"  # Qdrant counts as a vector DB
    assert _req(r, "LangGraph")["status"] == "missing"
    assert _req(r, "Kubernetes")["status"] == "listed"  # only in the skills line, never used in a bullet
    assert 0 < r["score"]["total"] < 100
    assert r["score"]["years"] == 1.0  # 2.5 years vs "2+ years"


def test_hallucinated_resume_skill_is_dropped(resume, jd):
    r = run(ScriptedLLM(), resume, jd)
    assert "Spark" not in r["profile"]["skills"]
    assert "Qdrant" not in r["profile"]["skills"] and "Vector Databases" in r["profile"]["skills"]


def test_guard_blocks_invented_claims(resume, jd):
    r = run(ScriptedLLM(), resume, jd)
    kept = [x["improved"] for x in r["suggestions"]["rewrites"]]
    assert len(kept) == 1 and "3,000" in kept[0]
    assert len(r["rejected"]) == 1
    assert "500" in r["rejected"][0]["reason"] and "LLM Evaluation" in r["rejected"][0]["reason"]


def test_falls_back_when_jd_extraction_fails(resume, jd):
    r = run(ScriptedLLM(broken_jd=True), resume, jd)
    skills = {q["skill"] for q in r["requirements"]}
    assert {"RAG", "LangGraph", "FastAPI", "Docker"} <= skills
    assert r["job"]["title"] == "this role"


def test_extractions_run_once_each(resume, jd):
    llm = ScriptedLLM()
    run(llm, resume, jd)
    assert sum(c.startswith("Read this job description") for c in llm.calls) == 1
    assert sum(c.startswith("Read this resume") for c in llm.calls) == 1


def test_weaker_fit_for_unrelated_role(resume):
    from pathlib import Path

    cv_jd = (Path(__file__).resolve().parent.parent / "samples" / "jd_cv_engineer.md").read_text()
    llm = ScriptedLLM(jd={"title": "CV Engineer", "must_have": ["Computer Vision", "PyTorch", "YOLO", "OpenCV",
                                                                "C++", "Docker"],
                          "nice_to_have": ["Kubernetes", "MLOps"]})
    genai, cv = run(ScriptedLLM(), resume, ""), run(llm, resume, cv_jd)
    assert cv["score"]["total"] < genai["score"]["total"]
    assert cv["score"]["years"] < 1.0  # 2.5 years vs "3-5 years"


def test_report_renders(resume, jd):
    md = to_markdown(run(ScriptedLLM(), resume, jd))
    assert md.startswith("# JobFit report: GenAI Engineer")
    assert "❌ | LangGraph" in md and "Suggested bullet rewrites" in md and "blocked" in md

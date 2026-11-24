from conftest import ROOT, ScriptedLLM
from fastapi.testclient import TestClient

import api


def test_analyze_endpoint():
    api.app.dependency_overrides[api.get_llm] = lambda: ScriptedLLM()
    client = TestClient(api.app)
    resume = (ROOT / "samples" / "resume_priya.md").read_bytes()

    r = client.post("/analyze", files={"resume": ("resume.md", resume, "text/markdown")},
                    data={"jd_text": (ROOT / "samples" / "jd_genai_engineer.md").read_text()})
    body = r.json()
    assert r.status_code == 200 and body["score"]["total"] > 0
    assert body["report_markdown"].startswith("# JobFit report")

    bad = client.post("/analyze", files={"resume": ("resume.exe", b"x", "application/octet-stream")},
                      data={"jd_text": "Python developer"})
    assert bad.status_code == 400
    missing = client.post("/analyze", files={"resume": ("resume.md", resume, "text/markdown")})
    assert missing.status_code == 400
    api.app.dependency_overrides.clear()

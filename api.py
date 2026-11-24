"""FastAPI service.

    uvicorn api:app --reload
    curl -F "resume=@resume.pdf" -F "jd=@job.txt" localhost:8000/analyze
"""
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile

from jobfit.config import Settings
from jobfit.graph import run
from jobfit.parse import load_text
from jobfit.report import to_markdown

app = FastAPI(title="JobFit", description="Honest resume vs job-description matching", version="1.0.0")


def get_llm():
    from jobfit.llm import get_llm as factory

    return factory(Settings())


LLM = Annotated[object, Depends(get_llm)]


def _read(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "file.txt").suffix.lower() or ".txt"
    if suffix not in {".pdf", ".md", ".txt"}:
        raise HTTPException(400, f"{upload.filename}: use .pdf, .md or .txt")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(upload.file.read())
    return load_text(tmp.name)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze_files(resume: UploadFile, llm: LLM, jd: UploadFile | None = None,
                  jd_text: Annotated[str | None, Form()] = None):
    job = jd_text or (_read(jd) if jd else None)
    if not job or not job.strip():
        raise HTTPException(400, "send a job description as a file (jd) or as text (jd_text)")
    result = run(llm, _read(resume), job)
    return {**{k: result[k] for k in ("job", "score", "requirements", "analysis", "suggestions", "rejected")},
            "report_markdown": to_markdown(result)}

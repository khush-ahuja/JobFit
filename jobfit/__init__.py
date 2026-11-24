"""JobFit: an honest resume vs job-description matcher built with LangGraph."""
from jobfit.config import Settings


def analyze(resume: str, jd: str, settings: Settings | None = None) -> dict:
    from jobfit.graph import run
    from jobfit.llm import get_llm

    return run(get_llm(settings or Settings()), resume, jd)

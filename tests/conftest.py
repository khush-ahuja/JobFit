import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class ScriptedLLM:
    """Deterministic stand-in for a chat model, keyed on which JobFit prompt it receives."""

    def __init__(self, jd=None, resume=None, rewrites=None, broken_jd=False):
        self.jd = jd or {"title": "GenAI Engineer", "must_have": ["Python", "LLMs", "RAG", "Vector Databases",
                                                                  "LangGraph", "FastAPI", "Docker"],
                         "nice_to_have": ["Kubernetes", "Fine-tuning", "LLM Evaluation"],
                         "responsibilities": ["build RAG systems"]}
        # "Spark" is a hallucination: it is not in the sample resume and must be dropped.
        self.resume = resume or {"name": "Priya Sharma", "years_experience": 2.5,
                                 "skills": ["Python", "PyTorch", "LangChain", "Qdrant", "Docker", "Spark"]}
        self.rewrites = rewrites if rewrites is not None else [
            {"original": "Deployed models as FastAPI services in Docker containers on AWS, serving 3,000 requests "
                         "per day",
             "improved": "Shipped production FastAPI services in Docker on AWS handling 3,000 requests per day"},
            {"original": "Wrote evaluation scripts to compare prompt versions on a 300-question test set",
             "improved": "Built RAGAS-based evaluation harness comparing prompt versions across 500 questions"},
        ]
        self.broken_jd = broken_jd
        self.calls = []

    def invoke(self, prompt):
        self.calls.append(prompt)
        if prompt.startswith("Read this job description"):
            reply = "sorry, I can't" if self.broken_jd else json.dumps(self.jd)
        elif prompt.startswith("Read this resume"):
            reply = json.dumps(self.resume)
        elif prompt.startswith("You are a hiring manager"):
            reply = json.dumps({"strengths": ["Built a production RAG pipeline with Qdrant"],
                                "gaps": ["No LangGraph"], "verdict": "good fit", "summary": "Solid RAG background."})
        elif prompt.startswith("Improve this resume"):
            body = {"rewrites": self.rewrites, "learn": [{"skill": "LangGraph", "how": "build a small agent"}]}
            reply = "```json\n" + json.dumps(body) + "\n```"
        else:
            raise AssertionError(prompt[:60])
        return SimpleNamespace(content=reply)


@pytest.fixture
def resume():
    return (ROOT / "samples" / "resume_priya.md").read_text()


@pytest.fixture
def jd():
    return (ROOT / "samples" / "jd_genai_engineer.md").read_text()

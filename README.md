# 🎯 JobFit: honest resume ↔ job-description matching

![tests](https://github.com/khush-ahuja/JobFit/actions/workflows/tests.yml/badge.svg)

Paste a job post, upload your resume, and JobFit tells you how well you fit. For every requirement it shows **the exact resume line that proves it**, flags skills you only *listed* but never showed using, rewrites your bullets in the job's language, and plans how to close the gaps.

Most resume tools pad resumes with keywords you don't have. JobFit has a **fabrication guard**: any suggested rewrite that adds a tool, number or claim missing from your original bullet is automatically blocked.

## How it works

```mermaid
flowchart LR
    S([Resume + JD]) --> J[Extract JD requirements<br/>LLM]
    S --> R[Extract resume facts<br/>LLM, verified against text]
    J --> M[Match + score<br/>deterministic]
    R --> M
    M --> A[Hiring-manager analysis<br/>LLM]
    A --> G[Suggest rewrites<br/>LLM]
    G --> F{Fabrication guard}
    F --> O([Report])
```

| Step | What it does |
|---|---|
| **Parallel extraction** | Two LangGraph branches structure the JD and the resume at the same time |
| **Hallucination check** | Skills the LLM claims are kept only if they literally appear in the resume |
| **Deterministic matching** | 40+ canonical skills with aliases (Qdrant/Pinecone → Vector Databases, k8s → Kubernetes); the same inputs always give the same score |
| **Evidence** | Each matched requirement links to the bullet that proves it; skills seen only in a skills list count as 🟡 *listed* (partial credit) |
| **Transparent score** | 60% must-have coverage + 25% nice-to-have + 15% years of experience |
| **Fabrication guard** | Drops rewrites that add any skill or number not in the original bullet |

## Real-model run

[`eval/run_eval.py`](eval/run_eval.py) runs the full pipeline 3 times per job on the sample resume, with `openai/gpt-oss-120b` on Groq (25 Nov 2026). Run it yourself with [`eval_colab.ipynb`](eval_colab.ipynb).

| Job | Fit score (3 runs) | Rewrites suggested | Blocked by the guard | LLM calls / run | Tokens / run |
|---|---|---|---|---|---|
| GenAI Engineer | 97, 97, 97 | 21 | 0 | 4 | 2,842 |
| Computer Vision Engineer | 29, 29, 29 | 21 | 0 | 4 | 3,087 |

- **Scores are reproducible.** The fit score is computed deterministically from the matched skills, so the LLM's run-to-run variation never changes it.
- **The guard blocked nothing in this run.** With a strong model and a well-written resume, none of the 42 suggested rewrites added a skill, tool or number. The guard is a safety net for weaker models and thinner resumes, not a filter that fires on every run. Its blocking behaviour is covered by the offline tests.
- A typical run takes about 3 seconds. The Computer Vision runs averaged 22 seconds because they hit API rate limits and waited.

## Quick start

```bash
git clone https://github.com/khush-ahuja/JobFit.git
cd JobFit
pip install -r requirements.txt
cp .env.example .env            # add GROQ_API_KEY (from console.groq.com)

python cli.py samples/resume_priya.md samples/jd_genai_engineer.md
streamlit run app.py            # web UI
uvicorn api:app --reload        # REST API at localhost:8000/docs
```

Runs on Groq, OpenAI or a fully local Ollama model (`LLM_PROVIDER=ollama`).

### API

```bash
curl -F "resume=@resume.pdf" -F "jd_text=$(cat job.txt)" localhost:8000/analyze
```

Returns the score breakdown, per-requirement status with evidence, analysis, rewrites, blocked rewrites and a Markdown report.

## Project structure

```
jobfit/
  graph.py    LangGraph pipeline: parallel extraction, match, analyze, suggest, guard
  skills.py   canonical skill vocabulary, aliases, context-aware extraction
  parse.py    PDF/Markdown loading, evidence lines, years-of-experience parsing
  report.py   Markdown report
  prompts.py  all prompts
cli.py · api.py · app.py
samples/      fictional resume and two job descriptions
tests/        offline tests with a scripted LLM (no API key needed)
```

## Tests

```bash
pytest
```

16 offline tests cover alias matching, ambiguous-word handling ("rest" vs REST APIs), skills-section detection, scoring, the hallucination check, the fabrication guard, the fallback when JD extraction fails, and the API.

"""Loading resumes / job descriptions and pulling out evidence lines."""
import re
from pathlib import Path


def load_text(path: str | Path) -> str:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        return "\n".join(p.extract_text() or "" for p in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def _is_list_line(line: str) -> bool:
    """True for keyword lists like 'Python, SQL, Docker, AWS' (a skills section, not proof of use)."""
    parts = [p.strip() for p in re.split(r"[,|;/·]", line) if p.strip()]
    return len(parts) >= 4 and sum(len(p.split()) <= 3 for p in parts) / len(parts) >= 0.8


def evidence_lines(resume: str) -> list[str]:
    """Bullet-like lines that describe work done, usable as evidence that a skill was applied.
    Skills-section keyword lists are excluded."""
    lines, in_skills = [], False
    for raw in resume.splitlines():
        line = re.sub(r"^[\s•●▪\-*–#]+", "", raw).strip()
        heading = raw.lstrip().startswith("#") or (line.isupper() and len(line) < 40)
        if heading:
            in_skills = "skill" in line.lower() or "technolog" in line.lower()
            continue
        if in_skills or len(line) < 25 or _is_list_line(line):
            continue
        lines.append(line)
    return lines


_YEARS = re.compile(r"(\d+)\s*\+?\s*(?:-|to)?\s*\d*\s*\+?\s*years?", re.I)


def years_required(jd: str) -> int | None:
    """Smallest 'N years' figure mentioned in the JD, e.g. '2-4 years of experience' -> 2."""
    nums = [int(m.group(1)) for m in _YEARS.finditer(jd) if int(m.group(1)) < 25]
    return min(nums) if nums else None

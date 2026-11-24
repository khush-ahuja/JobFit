"""Command-line JobFit.

    python cli.py samples/resume_priya.md samples/jd_genai_engineer.md
    python cli.py my_resume.pdf job.txt --out report.md
"""
import argparse
from pathlib import Path

from jobfit import analyze
from jobfit.parse import load_text
from jobfit.report import to_markdown


def main():
    p = argparse.ArgumentParser(description="Score a resume against a job description, honestly.")
    p.add_argument("resume", help="resume file (.pdf, .md or .txt)")
    p.add_argument("jd", help="job description file (.pdf, .md or .txt)")
    p.add_argument("--out", help="write the Markdown report here")
    args = p.parse_args()

    report = to_markdown(analyze(load_text(args.resume), load_text(args.jd)))
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"report written to {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()

"""Streamlit UI.

    streamlit run app.py
"""
import tempfile
from pathlib import Path

import streamlit as st

from jobfit import analyze
from jobfit.parse import load_text
from jobfit.report import to_markdown

st.set_page_config(page_title="JobFit", page_icon="🎯", layout="wide")
st.title("🎯 JobFit")
st.caption("Score your resume against a job description, see the evidence, "
           "and get rewrites that never invent anything.")

left, right = st.columns(2)
with left:
    up = st.file_uploader("Your resume", type=["pdf", "md", "txt"])
with right:
    jd = st.text_area("Job description", height=220, placeholder="Paste the job post here")

if st.button("Analyze", type="primary", disabled=not (up and jd.strip())):
    with tempfile.NamedTemporaryFile(suffix=Path(up.name).suffix, delete=False) as tmp:
        tmp.write(up.getvalue())
    with st.spinner("Reading the resume and the job post..."):
        result = analyze(load_text(tmp.name), jd)

    s = result["score"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fit score", f"{s['total']}/100")
    c2.metric("Must-have coverage", f"{s['must']:.0%}")
    c3.metric("Nice-to-have", f"{s['nice']:.0%}")
    c4.metric("Experience", f"{s['years']:.0%}")
    report = to_markdown(result)
    st.markdown(report)
    st.download_button("Download report (.md)", report, file_name="jobfit_report.md")

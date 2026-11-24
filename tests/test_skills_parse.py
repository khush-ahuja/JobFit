from jobfit.parse import evidence_lines, years_required
from jobfit.skills import extract_skills, normalise


def test_aliases_map_to_canonical_names():
    found = extract_skills("Built agents with LangGraph, stored embeddings in Qdrant, served with FastAPI on AWS")
    assert {"LangGraph", "Vector Databases", "Embeddings", "FastAPI", "AWS"} <= found
    assert "LangChain" not in found  # 'langgraph' must not be read as 'langchain'


def test_ambiguous_short_words_need_tech_context():
    assert "Machine Learning" not in extract_skills("I like ML.")  # lone 'ML' with no other tech nearby
    assert "Machine Learning" in extract_skills("ML models in PyTorch and scikit-learn")
    assert "REST APIs" not in extract_skills("Took a rest after the project.")


def test_cpp_and_word_boundaries():
    assert "C++" in extract_skills("Wrote C++ inference code with OpenCV")
    assert "Java" not in extract_skills("Uses JavaScript only")


def test_normalise_llm_names():
    assert normalise(["pinecone", "Large Language Models", "k8s", "Rust"]) == {
        "Vector Databases", "LLMs", "Kubernetes", "Rust"}


def test_years_required():
    assert years_required("Requires 3-5 years of experience") == 3
    assert years_required("2+ years in ML") == 2
    assert years_required("No experience needed") is None


def test_evidence_lines_strip_bullets():
    lines = evidence_lines("- Built a RAG pipeline over many documents\n• short\n● Deployed FastAPI services on AWS")
    assert lines == ["Built a RAG pipeline over many documents", "Deployed FastAPI services on AWS"]


def test_skills_section_is_not_evidence():
    text = ("## Experience\n- Deployed FastAPI services on AWS for clients\n\n"
            "## Skills\nPython, Kubernetes, Docker, Git, SQL\n")
    assert evidence_lines(text) == ["Deployed FastAPI services on AWS for clients"]
    assert evidence_lines("TOOLS: Python, Docker, Kubernetes, Git, SQL, Redis") == []

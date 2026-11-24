"""Skill vocabulary, normalisation and deterministic extraction.

Matching on a canonical vocabulary keeps the core score explainable and repeatable:
the same resume and job description always give the same coverage number.
"""
import re

# canonical name -> aliases (lower-case). Extend freely.
SKILLS: dict[str, list[str]] = {
    # languages
    "Python": ["python", "python3"],
    "Java": ["java"],
    "C++": ["c++", "cpp"],
    "SQL": ["sql", "mysql", "postgresql", "postgres", "sqlite"],
    "JavaScript": ["javascript", "js", "node.js", "nodejs", "typescript", "ts"],
    # ML / DL
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "dl", "neural networks"],
    "PyTorch": ["pytorch", "torch"],
    "TensorFlow": ["tensorflow", "keras", "tf"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "Computer Vision": ["computer vision", "cv", "image processing"],
    "NLP": ["nlp", "natural language processing"],
    "Transformers": ["transformers", "hugging face", "huggingface"],
    "OpenCV": ["opencv"],
    "YOLO": ["yolo", "yolov5", "yolov8", "yolov10"],
    "OCR": ["ocr", "textract", "tesseract", "document ai"],
    "Fine-tuning": ["fine-tuning", "fine tuning", "finetuning", "fine-tuned", "fine tuned", "fine-tune", "lora",
                    "qlora", "peft"],
    # GenAI
    "LLMs": ["llm", "llms", "large language models", "gpt-4", "gpt", "llama", "claude", "gemini", "mistral"],
    "RAG": ["rag", "retrieval-augmented generation", "retrieval augmented generation"],
    "Prompt Engineering": ["prompt engineering", "prompting", "dspy"],
    "LangChain": ["langchain"],
    "LangGraph": ["langgraph"],
    "LlamaIndex": ["llamaindex", "llama index", "llama-index"],
    "AI Agents": ["agents", "agentic", "agentic ai", "ai agents", "multi-agent", "tool calling", "function calling",
                  "react agent"],
    "Vector Databases": ["vector database", "vector databases", "vector db", "qdrant", "pinecone", "weaviate",
                         "chroma", "chromadb", "faiss", "milvus", "pgvector"],
    "Embeddings": ["embeddings", "embedding", "sentence-transformers", "semantic search"],
    "LLM Evaluation": ["evaluation", "evals", "ragas", "llm-as-a-judge", "llm as a judge"],
    # backend / mlops
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "REST APIs": ["rest", "rest api", "rest apis", "restful", "api development"],
    "Docker": ["docker", "containers", "containerization"],
    "Kubernetes": ["kubernetes", "k8s"],
    "CI/CD": ["ci/cd", "ci cd", "github actions", "jenkins", "continuous integration"],
    "Git": ["git", "github", "gitlab"],
    "MLOps": ["mlops", "mlflow", "model deployment", "model serving"],
    "Streamlit": ["streamlit", "gradio"],
    "Spark": ["spark", "pyspark"],
    "Pandas": ["pandas", "numpy"],
    # cloud / data
    "AWS": ["aws", "amazon web services", "sagemaker", "bedrock", "lambda", "s3"],
    "Azure": ["azure", "azure openai"],
    "GCP": ["gcp", "google cloud", "vertex ai"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
}

_ALIAS_TO_SKILL = {a: s for s, aliases in SKILLS.items() for a in aliases + [s.lower()]}
# Longest aliases first so "computer vision" wins over "cv", "langgraph" over "graph", etc.
_PATTERN = re.compile(
    r"(?<![a-z0-9+#])(" + "|".join(re.escape(a) for a in sorted(_ALIAS_TO_SKILL, key=len, reverse=True))
    + r")(?![a-z0-9+#])",
    re.I,
)
# Short aliases that are also ordinary words or ambiguous need nearby tech context to count.
_AMBIGUOUS = {"ml", "dl", "cv", "ts", "js", "tf", "rest", "agents", "evaluation", "git", "lambda", "s3", "gpt"}


def canonical(name: str) -> str | None:
    return _ALIAS_TO_SKILL.get(name.strip().lower())


def extract_skills(text: str) -> set[str]:
    found = set()
    for m in _PATTERN.finditer(text):
        alias = m.group(1).lower()
        if alias in _AMBIGUOUS and not _has_tech_context(text, m.start()):
            continue
        found.add(_ALIAS_TO_SKILL[alias])
    return found


def _has_tech_context(text: str, pos: int, window: int = 80) -> bool:
    nearby = text[max(0, pos - window): pos + window]
    return sum(1 for _ in _PATTERN.finditer(nearby)) >= 2


def normalise(skills) -> set[str]:
    """Maps free-text skill names (e.g. from an LLM) onto the canonical vocabulary where possible."""
    out = set()
    for s in skills:
        c = canonical(s) or next(iter(extract_skills(s)), None)
        out.add(c or s.strip())
    return {s for s in out if s}

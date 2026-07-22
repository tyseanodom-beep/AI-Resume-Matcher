"""
resume_matcher.py

Core, UI-agnostic analysis logic for the AI Resume Matcher.

Provides:
    - normalize_text / tokenize          -> text cleanup helpers
    - keyword_overlap                    -> % of job keywords found in resume
    - find_skills                        -> known-skill detection
    - score_message                      -> human-readable score label
    - calculate_scores                   -> lightweight scoring (used by tests)
    - analyze                            -> full analysis, returns a MatchResult
    - build_report                       -> plain-text downloadable report
    - extract_resume_text                -> reads .txt / .pdf / .docx resumes,
                                             accepting either a single path
                                             (extract_resume_text(path)) or the
                                             three-argument Streamlit upload
                                             form (extract_resume_text(filename,
                                             file_obj, file_bytes))
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Optional, Union


# ==========================================================
# Exceptions
# ==========================================================

class UnsupportedFileTypeError(Exception):
    """Raised when the uploaded resume isn't a supported file type."""


class EmptyResumeTextError(Exception):
    """Raised when no extractable text could be found in the resume."""


# ==========================================================
# Reference data
# ==========================================================

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to",
    "for", "of", "with", "by", "is", "are", "was", "were", "be", "been",
    "being", "this", "that", "these", "those", "as", "from", "it", "its",
    "you", "your", "we", "our", "will", "shall", "can", "should", "would",
    "must", "have", "has", "had", "not", "no", "yes", "into", "about",
    "than", "then", "so", "such", "also", "any", "all", "each", "other",
    "up", "out", "over", "under", "again", "further", "once", "here",
    "there", "when", "where", "why", "how", "both", "more", "most",
}

SKILLS_DB = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go",
    "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R",
    "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis",
    "AWS", "Azure", "GCP", "Google Cloud", "Terraform", "Ansible",
    "Docker", "Kubernetes", "Jenkins", "CI/CD", "Git", "GitHub",
    "Linux", "Bash", "Shell Scripting",
    "React", "Angular", "Vue", "Node.js", "Flask", "Django", "FastAPI",
    "HTML", "CSS",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "NumPy",
    "Data Analysis", "Data Science", "Data Engineering",
    "REST API", "GraphQL", "Microservices",
    "Agile", "Scrum", "Jira",
    "Tableau", "Power BI", "Excel",
    "Hadoop", "Spark", "Airflow",
]


# ==========================================================
# Text helpers
# ==========================================================

def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list:
    """Split normalized text into a list of word tokens."""
    normalized = normalize_text(text)
    if not normalized:
        return []
    return normalized.split(" ")


# ==========================================================
# Scoring helpers
# ==========================================================

def keyword_overlap(resume_text: str, job_text: str) -> float:
    """Percentage of meaningful job-description keywords found in the resume."""
    job_tokens = set(tokenize(job_text)) - STOPWORDS
    if not job_tokens:
        return 0

    resume_tokens = set(tokenize(resume_text)) - STOPWORDS
    if not resume_tokens:
        return 0

    matched = job_tokens & resume_tokens
    return round(len(matched) / len(job_tokens) * 100, 2)


def find_skills(text: str) -> list:
    """Return the known skills (canonical capitalization) mentioned in text."""
    if not text:
        return []

    text_lower = text.lower()
    found = []
    for skill in SKILLS_DB:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.lower()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def score_message(score: float) -> str:
    """Human-readable label for a 0-100 match score."""
    if score >= 90:
        return "Excellent match! Your resume aligns strongly with this role."
    if score >= 75:
        return "Strong match. A few tweaks could make this even better."
    if score >= 50:
        return "Moderate match. Consider addressing the gaps below."
    if score > 0:
        return "Weak match. Significant tailoring is recommended."
    return "No meaningful match found. Add relevant skills and keywords."


def compute_formatting_score(resume_text: str) -> float:
    """Lightweight heuristic for resume structure/formatting quality."""
    if not resume_text or not resume_text.strip():
        return 0

    text_lower = resume_text.lower()
    score = 0

    section_keywords = [
        "experience", "education", "skills", "summary",
        "projects", "certification",
    ]
    found_sections = sum(1 for kw in section_keywords if kw in text_lower)
    score += min(found_sections, 4) * 15  # up to 60

    word_count = len(resume_text.split())
    if 150 <= word_count <= 1200:
        score += 25
    elif word_count > 0:
        score += 10

    if any(line.strip().startswith(("-", "•", "*")) for line in resume_text.splitlines()):
        score += 15

    return float(min(100, score))


def calculate_scores(resume_text: str, job_text: str) -> dict:
    """Lightweight scoring used directly by the test suite."""
    resume_text = resume_text or ""
    job_text = job_text or ""

    if not resume_text.strip() or not job_text.strip():
        return {"match_score": 0, "skills_found": []}

    resume_skills = find_skills(resume_text)
    job_skills = find_skills(job_text)

    skills_found = [skill for skill in job_skills if skill in resume_skills]
    skill_score = (len(skills_found) / len(job_skills) * 100) if job_skills else 0
    kw_score = keyword_overlap(resume_text, job_text)

    match_score = round(skill_score * 0.6 + kw_score * 0.4)
    match_score = max(0, min(100, match_score))

    return {"match_score": match_score, "skills_found": skills_found}


# ==========================================================
# Result container
# ==========================================================

class MatchResult(dict):
    """
    Dict-like analysis result.

    Behaves like a plain dict (so result["match_score"] works, matching the
    test suite), while also exposing the richer attributes app.py relies on
    (result.scores, result.matching_skills, etc.).
    """

    def __init__(self, data: dict):
        super().__init__(data)
        self.scores: dict = {}
        self.matching_skills: list = []
        self.missing_skills: list = []
        self.matching_keywords: list = []
        self.missing_keywords: list = []
        self.summary: str = ""
        self.recommendations: list = []


def _build_summary(overall: int, matching_skills: list, missing_skills: list) -> str:
    if matching_skills:
        skills_note = f"It aligns well on {', '.join(matching_skills[:5])}."
    else:
        skills_note = "It doesn't clearly show the skills this role is looking for."

    if missing_skills:
        gap_note = f" Consider adding evidence of {', '.join(missing_skills[:5])}."
    else:
        gap_note = " No major required skills appear to be missing."

    return f"Overall match: {overall}%. {skills_note}{gap_note}"


def _build_recommendations(missing_skills: list, formatting_score: float, keywords_score: float) -> list:
    recommendations = []

    if missing_skills:
        shown = ", ".join(missing_skills[:5])
        recommendations.append(f"Add or highlight experience with: {shown}.")

    if keywords_score < 50:
        recommendations.append(
            "Mirror more of the job description's exact language and terminology."
        )

    if formatting_score < 60:
        recommendations.append(
            "Use clear section headers (Experience, Education, Skills) and bullet points."
        )

    if not recommendations:
        recommendations.append("Your resume is well-aligned with this job description.")

    return recommendations


def analyze(resume_text: str, job_text: str) -> MatchResult:
    """Full analysis used by the Streamlit app."""
    resume_text = resume_text or ""
    job_text = job_text or ""

    formatting_score = compute_formatting_score(resume_text)

    if not resume_text.strip() or not job_text.strip():
        result = MatchResult({
            "match_score": 0,
            "skills_found": [],
            "message": "Provide both a resume and a job description to run the analysis.",
        })
        result.scores = {
            "overall": 0,
            "skills": 0,
            "keywords": 0,
            "formatting": round(formatting_score),
        }
        result.missing_skills = find_skills(job_text)
        result.summary = result["message"]
        result.recommendations = ["Add a resume and a job description to see tailored recommendations."]
        return result

    resume_skills = find_skills(resume_text)
    job_skills = find_skills(job_text)
    matching_skills = [skill for skill in job_skills if skill in resume_skills]
    missing_skills = [skill for skill in job_skills if skill not in resume_skills]

    keywords_score = keyword_overlap(resume_text, job_text)
    resume_tokens = set(tokenize(resume_text)) - STOPWORDS
    job_tokens = set(tokenize(job_text)) - STOPWORDS
    matching_keywords = sorted(job_tokens & resume_tokens)
    missing_keywords = sorted(job_tokens - resume_tokens)

    skills_score = (len(matching_skills) / len(job_skills) * 100) if job_skills else 0

    overall = round(skills_score * 0.5 + keywords_score * 0.3 + formatting_score * 0.2)
    overall = max(0, min(100, overall))

    message = score_message(overall)

    result = MatchResult({
        "match_score": overall,
        "skills_found": matching_skills,
        "message": message,
    })
    result.scores = {
        "overall": overall,
        "skills": round(skills_score),
        "keywords": round(keywords_score),
        "formatting": round(formatting_score),
    }
    result.matching_skills = matching_skills
    result.missing_skills = missing_skills
    result.matching_keywords = matching_keywords[:30]
    result.missing_keywords = missing_keywords[:30]
    result.summary = _build_summary(overall, matching_skills, missing_skills)
    result.recommendations = _build_recommendations(missing_skills, formatting_score, keywords_score)
    return result


def build_report(filename: str, result: MatchResult) -> str:
    """Plain-text report suitable for a Streamlit download_button."""
    scores = getattr(result, "scores", {}) or {}
    matching_skills = getattr(result, "matching_skills", []) or result.get("skills_found", [])
    missing_skills = getattr(result, "missing_skills", []) or []
    matching_keywords = getattr(result, "matching_keywords", []) or []
    missing_keywords = getattr(result, "missing_keywords", []) or []
    summary = getattr(result, "summary", "") or result.get("message", "")
    recommendations = getattr(result, "recommendations", []) or []

    lines = [
        "AI RESUME MATCHER — ANALYSIS REPORT",
        "=" * 40,
        f"Resume file: {filename}",
        "",
        f"Overall Match: {scores.get('overall', result.get('match_score', 0))}%",
        f"Skill Match: {scores.get('skills', '-')}%",
        f"Keyword Match: {scores.get('keywords', '-')}%",
        f"Resume Structure: {scores.get('formatting', '-')}%",
        "",
        "Summary",
        "-" * 40,
        summary,
        "",
        "Matching Skills",
        "-" * 40,
        ", ".join(matching_skills) if matching_skills else "None found.",
        "",
        "Missing Skills",
        "-" * 40,
        ", ".join(missing_skills) if missing_skills else "None.",
        "",
        "Matching ATS Keywords",
        "-" * 40,
        ", ".join(matching_keywords) if matching_keywords else "None found.",
        "",
        "Missing Keywords",
        "-" * 40,
        ", ".join(missing_keywords) if missing_keywords else "None.",
        "",
        "Recommendations",
        "-" * 40,
    ]
    lines.extend(f"- {rec}" for rec in recommendations) if recommendations else lines.append("None.")

    return "\n".join(lines)


# ==========================================================
# Resume text extraction
# ==========================================================

def _extract_pdf_text(data: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
    except ImportError as error:
        raise UnsupportedFileTypeError(
            "PDF support requires PyPDF2. Install it with `pip install PyPDF2`."
        ) from error

    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx_text(data: bytes) -> str:
    try:
        import docx
    except ImportError as error:
        raise UnsupportedFileTypeError(
            "DOCX support requires python-docx. Install it with `pip install python-docx`."
        ) from error

    document = docx.Document(io.BytesIO(data))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def extract_resume_text(
    filename: Union[str, Path],
    file_obj: Optional[object] = None,
    file_bytes: Optional[bytes] = None,
) -> str:
    """
    Extract text from a resume file.

    Supports two calling conventions:
      - extract_resume_text(path)                      -> reads directly from disk
      - extract_resume_text(name, file_obj, file_bytes) -> reads from an
        in-memory upload (e.g. a Streamlit UploadedFile)
    """
    if file_obj is None and file_bytes is None:
        path = Path(filename)
        name = path.name
        ext = path.suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(f"Unsupported file type: '{ext or 'unknown'}'.")

        if ext == ".txt":
            text = path.read_text(encoding="utf-8")
        elif ext == ".pdf":
            text = _extract_pdf_text(path.read_bytes())
        else:  # .docx
            text = _extract_docx_text(path.read_bytes())
    else:
        name = str(filename)
        ext = Path(name).suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(f"Unsupported file type: '{ext or 'unknown'}'.")

        data = file_bytes if file_bytes is not None else file_obj.read()

        if ext == ".txt":
            text = data.decode("utf-8") if isinstance(data, bytes) else data
        elif ext == ".pdf":
            text = _extract_pdf_text(data)
        else:  # .docx
            text = _extract_docx_text(data)

    if not text or not text.strip():
        raise EmptyResumeTextError("No extractable text found in the uploaded resume.")

    return text
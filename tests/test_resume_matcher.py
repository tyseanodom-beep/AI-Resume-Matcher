"""
Professional unit tests for resume_matcher.py

Run with:
    python3 -m pytest tests/ -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from resume_matcher import (
    analyze,
    calculate_scores,
    extract_resume_text,
    find_skills,
    keyword_overlap,
    normalize_text,
    score_message,
    tokenize,
    EmptyResumeTextError,
    UnsupportedFileTypeError,
)


# ==========================================================
# normalize_text
# ==========================================================

def test_normalize_text_lowercases():
    assert normalize_text("HELLO WORLD") == "hello world"


def test_normalize_text_removes_punctuation():
    assert normalize_text("Python, SQL & AWS!!") == "python sql aws"


def test_normalize_text_collapses_spaces():
    assert normalize_text("python      sql\n\naws") == "python sql aws"


def test_normalize_text_empty():
    assert normalize_text("") == ""


# ==========================================================
# tokenize
# ==========================================================

def test_tokenize_returns_list():
    tokens = tokenize("Python SQL Docker")

    assert isinstance(tokens, list)


def test_tokenize_contains_words():
    tokens = tokenize("Python SQL Docker")

    assert "python" in tokens
    assert "sql" in tokens
    assert "docker" in tokens


def test_tokenize_empty():
    assert tokenize("") == []

# ==========================================================
# keyword_overlap
# ==========================================================

def test_keyword_overlap_full():
    resume = "python sql docker aws"
    job = "python sql docker aws"

    score = keyword_overlap(resume, job)

    assert score == pytest.approx(100.0)


def test_keyword_overlap_partial():
    resume = "python sql"

    job = "python sql aws docker"

    score = keyword_overlap(resume, job)

    assert score == pytest.approx(50.0)


def test_keyword_overlap_none():
    score = keyword_overlap(
        "marketing sales",
        "python sql docker",
    )

    assert score == 0


# ==========================================================
# find_skills
# ==========================================================

def test_find_skills_detects_multiple():
    text = """
    Python SQL AWS Docker Kubernetes Git Linux
    """

    skills = find_skills(text)

    assert "Python" in skills
    assert "SQL" in skills
    assert "AWS" in skills
    assert "Docker" in skills


def test_find_skills_empty():
    assert find_skills("") == []


# ==========================================================
# score_message
# ==========================================================

def test_score_message_high():
    message = score_message(95)

    assert "Excellent" in message


def test_score_message_medium():
    message = score_message(65)

    assert isinstance(message, str)


def test_score_message_low():
    message = score_message(20)

    assert isinstance(message, str)


# ==========================================================
# calculate_scores
# ==========================================================

def test_calculate_scores_keys():
    result = calculate_scores(
        "Python SQL AWS",
        "Python SQL AWS Docker",
    )

    assert "match_score" in result
    assert "skills_found" in result
    assert isinstance(result["skills_found"], list)

    # ==========================================================
# analyze
# ==========================================================

def test_analyze_returns_dictionary():
    result = analyze(
        "Python SQL AWS Docker",
        "Looking for Python, SQL, AWS, and Docker experience.",
    )

    assert isinstance(result, dict)


def test_analyze_contains_expected_keys():
    result = analyze(
        "Python SQL AWS",
        "Python developer with SQL and AWS experience.",
    )

    assert "match_score" in result
    assert "skills_found" in result
    assert "message" in result


def test_analyze_match_score_range():
    result = analyze(
        "Python SQL",
        "Python SQL AWS Docker",
    )

    assert 0 <= result["match_score"] <= 100


def test_analyze_empty_resume_text():
    result = analyze(
        "",
        "Python SQL AWS",
    )

    assert result["match_score"] == 0


def test_analyze_empty_job_description():
    result = analyze(
        "Python SQL AWS",
        "",
    )

    assert result["match_score"] == 0


# ==========================================================
# extract_resume_text
# ==========================================================

def test_extract_resume_text_txt(tmp_path):
    resume_file = tmp_path / "resume.txt"
    resume_file.write_text(
        "Python developer with SQL and AWS experience.",
        encoding="utf-8",
    )

    text = extract_resume_text(resume_file)

    assert "Python developer" in text
    assert "SQL" in text


def test_extract_resume_text_unsupported_file(tmp_path):
    resume_file = tmp_path / "resume.jpg"
    resume_file.write_bytes(b"fake image content")

    with pytest.raises(UnsupportedFileTypeError):
        extract_resume_text(resume_file)


def test_extract_resume_text_empty_file(tmp_path):
    resume_file = tmp_path / "empty.txt"
    resume_file.write_text("", encoding="utf-8")

    with pytest.raises(EmptyResumeTextError):
        extract_resume_text(resume_file)

    # ==========================================================
# Additional edge cases
# ==========================================================

def test_keyword_overlap_ignores_case():
    score = keyword_overlap(
        "PYTHON SQL AWS",
        "python sql aws",
    )

    assert score == pytest.approx(100.0)


def test_keyword_overlap_ignores_punctuation():
    score = keyword_overlap(
        "Python, SQL, AWS!",
        "Python SQL AWS",
    )

    assert score == pytest.approx(100.0)


def test_keyword_overlap_empty_resume():
    score = keyword_overlap(
        "",
        "Python SQL AWS",
    )

    assert score == 0


def test_keyword_overlap_empty_job_description():
    score = keyword_overlap(
        "Python SQL AWS",
        "",
    )

    assert score == 0


def test_find_skills_does_not_return_duplicates():
    skills = find_skills(
        "Python python PYTHON SQL sql AWS aws"
    )

    assert skills.count("Python") == 1
    assert skills.count("SQL") == 1
    assert skills.count("AWS") == 1


def test_calculate_scores_match_score_range():
    result = calculate_scores(
        "Python SQL AWS",
        "Python SQL AWS Docker Kubernetes",
    )

    assert 0 <= result["match_score"] <= 100


def test_calculate_scores_returns_dictionary():
    result = calculate_scores(
        "Python developer",
        "Python software engineer",
    )

    assert isinstance(result, dict)


def test_analyze_message_is_string():
    result = analyze(
        "Python SQL AWS",
        "Python SQL AWS Docker",
    )

    assert isinstance(result["message"], str)
    assert result["message"]


def test_extract_resume_text_preserves_content(tmp_path):
    resume_file = tmp_path / "resume.txt"
    expected_text = """
    Tysean Odom
    Python Developer
    Skills: Python, SQL, AWS, Docker
    """

    resume_file.write_text(expected_text, encoding="utf-8")

    extracted_text = extract_resume_text(resume_file)

    assert "Tysean Odom" in extracted_text
    assert "Python Developer" in extracted_text
    assert "Docker" in extracted_text
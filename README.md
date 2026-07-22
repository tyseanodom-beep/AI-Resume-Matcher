# 🎯 AI Resume Matcher

A Streamlit web application that analyzes how well a resume matches a job description using ATS-style keyword and skill matching. It generates an ATS compatibility score, identifies missing skills and keywords, and provides personalized recommendations to improve your resume before applying.

## 🚀 Features

- 📄 Upload PDF and DOCX resumes
- 📝 Paste any job description
- 🎯 ATS-style match score (0–100)
- 🔍 Skill gap analysis
- 🏷️ Keyword overlap detection
- 💡 Personalized resume improvement recommendations
- 📊 Overall, skill, keyword, and formatting scores
- 📥 Download a detailed analysis report
- 🔒 Privacy-first — all processing happens locally with no external API calls

## 🛠️ Tech Stack

- Python
- Streamlit
- PyPDF2
- python-docx
- pytest

## 🏗️ Architecture

```
app.py
│
├── resume_matcher.py    # Resume analysis engine
├── app.py               # Streamlit user interface
├── tests/               # Unit tests
└── requirements.txt
```

The application separates the user interface from the analysis engine, making the core logic reusable, easy to test, and simple to extend.

## 📈 How It Works

1. Upload your resume (PDF or DOCX).
2. Paste the job description.
3. The app extracts the resume text.
4. Skills and ATS keywords are compared against the job posting.
5. An overall compatibility score is generated.
6. Missing skills, missing keywords, and improvement recommendations are displayed.
7. Download a complete ATS analysis report.

## 📊 Scoring Breakdown

| Category | Weight |
|----------|--------|
| Skill Match | 60% |
| Keyword Match | 30% |
| Resume Formatting | 10% |

## 🎯 Why I Built This

Applying for jobs often means tailoring your resume for every application. It can be difficult to know exactly what an Applicant Tracking System (ATS) is looking for.

I built AI Resume Matcher to help job seekers instantly compare their resume against a job description, identify missing skills and keywords, and receive actionable recommendations—all while keeping their data private.

## 🚀 Future Improvements

- AI-powered resume rewriting
- Cover letter generation
- OCR support for scanned resumes
- Resume history and saved analyses
- Industry-specific skill libraries
- Cloud deployment with user accounts

## ⚠️ Disclaimer

This tool provides an estimated ATS-style comparison and is intended for educational purposes. It does not guarantee interviews or hiring outcomes.

## 👨‍💻 Author

**Tysean Odom**

- Computer Science Student
- CompTIA Network+ Certified
- Aspiring Machine Learning Engineer

---

⭐ If you found this project helpful, consider giving it a star!

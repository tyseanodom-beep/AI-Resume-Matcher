"""
AI Resume Matcher — Streamlit front end.

Upload a resume (PDF/DOCX) and paste a job description to get an
ATS-style match score, skill gap analysis, and improvement recommendations.

All analysis logic lives in resume_matcher.py so it can be tested and
reused independently of this UI. Run with:

    streamlit run app.py
"""

import streamlit as st

from resume_matcher import (
    EmptyResumeTextError,
    UnsupportedFileTypeError,
    analyze,
    build_report,
    extract_resume_text,
    score_message,
)


st.set_page_config(
    page_title="AI Resume Matcher",
    page_icon="🎯",
    layout="wide",
)

st.markdown(
    """
     <style>
        .main-title { font-size: 2.7rem; font-weight: 800; margin-bottom: 0; }
        .subtitle { color: #9aa0a6; margin-bottom: 2rem; }
        .skill-chip {
        display: inline-block;
        padding: 0.35rem 0.65rem;
        margin: 0.2rem;
        border-radius: 999px;
        background: rgba(49, 130, 206, 0.18);
        border: 1px solid rgba(49, 130, 206, 0.45);
    }
</style>
""",
unsafe_allow_html=True,
)

with st.sidebar:
    st.header("About")
    st.write(
        "AI Resume Matcher scores how well a resume aligns with a job "
        "description using ATS-style keyword and skill matching — no "
        "external API calls, so your resume never leaves this session."
    )
    st.write("**Built with:** Python, Streamlit, PyPDF2, python-docx")
    st.write("**Author:** Tysean Odom")
    st.markdown("[GitHub Repo](#) · [LinkedIn](https://linkedin.com/in/tysean-odom)")

st.markdown('<p class="main-title">🎯 AI Resume Matcher</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Analyze resume alignment, ATS keywords, skills, '
    "and improvement areas.</p>",
    unsafe_allow_html=True,
)

uploaded_resume = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx"],
    help="Upload a text-based PDF or Microsoft Word document.",
)

job_text = st.text_area(
    "Paste the complete job description",
    height=280,
    placeholder=(
        "Paste the full responsibilities, qualifications, and required "
        "skills here..."
    ),
)

analyze_clicked = st.button(
    "Analyze Resume",
    type="primary",
    use_container_width=True,
)

if analyze_clicked:
    if uploaded_resume is None:
        st.warning("Upload a PDF or DOCX resume first.")
        st.stop()

    if not job_text.strip():
        st.warning("Paste the complete job description first.")
        st.stop()

    try:
        resume_text = extract_resume_text(
            uploaded_resume.name,
            uploaded_resume,
            uploaded_resume.getvalue(),
        )
    except UnsupportedFileTypeError as error:
        st.error(str(error))
        st.stop()
    except EmptyResumeTextError as error:
        st.error(str(error))
        st.stop()
    except Exception as error:  # noqa: BLE001 - surface unexpected parse errors
        st.error(f"The resume could not be read: {error}")
        st.stop()

    with st.spinner("Analyzing resume against job description..."):
        result = analyze(resume_text, job_text)
        report = build_report(uploaded_resume.name, result)

    st.success("Resume analysis complete.")

    st.subheader("ATS Match Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Overall Match",
        f'{result.scores["overall"]}%',
        score_message(result.scores["overall"]),
    )
    col2.metric("Skill Match", f'{result.scores["skills"]}%')
    col3.metric("Keyword Match", f'{result.scores["keywords"]}%')
    col4.metric("Resume Structure", f'{result.scores["formatting"]}%')

    st.progress(result.scores["overall"] / 100)

    st.subheader("Resume Summary")
    st.info(result.summary)

    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("✅ Matching Skills")
        if result.matching_skills:
            st.markdown(
            "".join(
                f'<span class="skill-chip">{skill}</span>'
                for skill in result.matching_skills
         ),
        unsafe_allow_html=True,
    )
        else:   
            st.write("No recognized job skills matched.")

    with right_column:
        st.subheader("⚠️ Missing Skills")
        if result.missing_skills:
            for skill in result.missing_skills:
                st.write(f"- {skill}")
        else:
            st.write("No recognized required skills are missing.")

    st.subheader("Matching ATS Keywords")
    st.write(
        ", ".join(result.matching_keywords)
        if result.matching_keywords
        else "No meaningful matching keywords were found."
    )

    with st.expander("View additional missing keywords"):
        st.write(
            ", ".join(result.missing_keywords)
            if result.missing_keywords
            else "No additional missing keywords were found."
)

    st.subheader("Resume Improvement Recommendations")
    for recommendation in result.recommendations:
        st.write(f"• {recommendation}")

    st.download_button(
        label="Download Analysis Report",
        data=report,
        file_name="resume_match_report.txt",
        mime="text/plain",
        use_container_width=True,
)

    with st.expander("View extracted resume text"):
        st.text(resume_text[:10000])

st.caption(
    "This tool provides an estimated ATS-style comparison and does not "
    "guarantee an interview or hiring decision."
)
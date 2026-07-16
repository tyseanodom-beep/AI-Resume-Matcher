import streamlit as st

st.set_page_config(page_title="AI Resume Matcher", page_icon="📄")

st.title("📄 AI Resume Matcher")

resume_text = st.text_area("Paste Resume Here", height=200)

job_text = st.text_area("Paste Job Description Here", height=200)

if st.button("Analyze Match"):
    if resume_text and job_text:
        st.success("Analysis Complete!")

        resume_words = set(resume_text.lower().split())
        job_words = set(job_text.lower().split())

        matching = resume_words.intersection(job_words)

        score = int((len(matching) / max(len(job_words), 1)) * 100)

        st.metric("Match Score", f"{score}%")

        st.subheader("Matching Keywords")
        st.write(list(matching)[:20])

    else:
        st.warning("Please enter both resume and job description.")
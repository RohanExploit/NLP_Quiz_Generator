import streamlit as st
import spacy
import random
import pdfplumber
import os
import tempfile
import nltk
from nltk.corpus import wordnet

# ------------- NLTK / SpaCy Initialization -------------
@st.cache_resource
def load_resources():
    """Download and cache NLTK data + SpaCy model."""
    for res, path in [('wordnet', 'corpora/wordnet'), ('omw-1.4', 'corpora/omw-1.4')]:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(res, quiet=True)
    nlp = spacy.load('en_core_web_sm')
    return nlp

# ------------- Core NLP Functions (unchanged) ----------
def extract_pdf_text(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            return "".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        return None

def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            s = lemma.name().replace('_', ' ')
            if s.lower() != word.lower():
                synonyms.add(s)
    return list(synonyms)

def generate_mcqs(text, nlp, num_questions=5):
    if not text:
        return []

    doc = nlp(text)
    sentences = [
        sent.text.strip() for sent in doc.sents
        if 15 < len(sent.text.strip()) <= 200 and not any(c.isdigit() for c in sent.text.strip())
    ]
    if not sentences:
        return []

    generated_questions = set()
    mcqs = []
    max_attempts = num_questions * 20
    attempts = 0

    while len(mcqs) < num_questions and attempts < max_attempts:
        attempts += 1
        sentence = random.choice(sentences)
        sent_doc = nlp(sentence)
        nouns = [t.text for t in sent_doc if t.pos_ in ["NOUN", "PROPN"]]
        if not nouns:
            continue

        subject = random.choice(nouns)
        question_stem = sentence.replace(subject, "_______", 1)
        if (question_stem, subject) in generated_questions:
            continue

        synonyms = get_synonyms(subject)
        similar_words = [
            t.text for t in nlp.vocab
            if t.is_alpha and t.has_vector and t.is_lower
            and t.similarity(nlp(subject)) > 0.5
        ][:3]

        distractors = list(set(synonyms + similar_words))
        distractors = [d for d in distractors if d.lower() != subject.lower()]

        remaining_nouns = [
            t.text for t in nlp(text)
            if t.pos_ in ["NOUN", "PROPN"]
            and t.text.lower() != subject.lower()
            and t.text.lower() not in [d.lower() for d in distractors]
        ]
        while len(distractors) < 3 and remaining_nouns:
            distractors.append(random.choice(remaining_nouns))

        if len(distractors) < 3:
            continue

        choices = [subject] + random.sample(distractors, 3)
        random.shuffle(choices)

        # Filter trivial or duplicate choices
        if any(len(c) <= 1 for c in choices):
            continue
        if len(set(c.lower() for c in choices)) < 4:
            continue

        correct_idx = choices.index(subject)
        correct_letter = chr(65 + correct_idx)
        mcqs.append({
            "question": question_stem,
            "choices": choices,
            "answer": correct_letter,
            "answer_text": subject
        })
        generated_questions.add((question_stem, subject))

    return mcqs

# ------------- Streamlit App --------------------
st.set_page_config(
    page_title="QuizZable – NLP Quiz Generator",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Global CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700&family=Inter:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0f172a;
    color: #f8fafc;
}

section.main > div {
    padding-top: 2rem !important;
}

h1 { 
    font-family: 'Outfit', sans-serif !important; 
    font-size: 2.5rem !important;
    background: linear-gradient(to right, #fff, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
}

h2, h3 { font-family: 'Outfit', sans-serif !important; }

.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #4c1d95) !important;
    color: white !important;
    border: none !important;
    border-radius: 1rem !important;
    padding: 0.75rem 2rem !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}
.stButton > button:hover {
    filter: brightness(1.15) !important;
    transform: translateY(-1px) !important;
}

.stProgress > div > div > div {
    background: linear-gradient(to right, #7c3aed, #2dd4bf) !important;
    border-radius: 4px !important;
}

.quiz-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 1.25rem;
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 30px -10px rgba(0,0,0,0.4);
}

.score-badge {
    background: rgba(45, 212, 191, 0.12);
    border: 1px solid rgba(45, 212, 191, 0.3);
    border-radius: 1rem;
    padding: 1rem 2rem;
    text-align: center;
    font-size: 2rem;
    font-weight: 700;
    font-family: 'Outfit', sans-serif;
    color: #2dd4bf;
}

.correct-answer { 
    color: #10b981; 
    font-weight: 600; 
}

.wrong-answer { 
    color: #ef4444; 
    font-weight: 600; 
}

div[data-testid="stFileUploader"] {
    border: 2px dashed rgba(255,255,255,0.2);
    border-radius: 1rem;
    padding: 1rem;
    background: rgba(255,255,255,0.02);
}

.stNumberInput input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 0.75rem !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ----------- Session State Init -------------------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "mcqs" not in st.session_state:
    st.session_state.mcqs = []
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answers" not in st.session_state:
    st.session_state.answers = []
if "answered" not in st.session_state:
    st.session_state.answered = False

# ----------- Load model once ----------------------
nlp = load_resources()

# ============================================================
# PAGE: HOME
# ============================================================
def page_home():
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("<div style='text-align:center; font-size: 5rem; line-height:1;'>🧠</div>", unsafe_allow_html=True)
        st.markdown("<h1>NLP Quiz Generator</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center; color:#94a3b8; font-size:1.1rem;'>Transform any PDF into an engaging quiz using AI & NLP</p>",
            unsafe_allow_html=True
        )
        st.markdown("---")
        
        with st.container():
            st.markdown('<div class="quiz-card">', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("📄 Upload your PDF", type=["pdf"], label_visibility="visible")
            num_questions = st.number_input("Number of questions", min_value=1, max_value=50, value=5, step=1)

            if st.button("🚀 Generate Quiz"):
                if uploaded_file is None:
                    st.error("Please upload a PDF file first.")
                else:
                    with st.spinner("🧠 AI is reading your document..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(uploaded_file.read())
                            tmp_path = tmp.name

                        text = extract_pdf_text(tmp_path)
                        os.unlink(tmp_path)

                        if not text or len(text.strip()) < 100:
                            st.error("Couldn't extract enough text from this PDF. Try a different file.")
                        else:
                            mcqs = generate_mcqs(text, nlp, num_questions=int(num_questions))
                            if not mcqs:
                                st.error("Couldn't generate questions. The PDF may not have enough clear sentences.")
                            else:
                                st.session_state.mcqs = mcqs
                                st.session_state.current_q = 0
                                st.session_state.score = 0
                                st.session_state.answers = []
                                st.session_state.answered = False
                                st.session_state.page = "quiz"
                                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style='text-align:center; margin-top: 3rem; color: #475569; font-size: 0.85rem;'>
            Built by <a href='https://github.com/RohanExploit' style='color:#7c3aed;'>RohanExploit</a> • Powered by SpaCy & NLTK
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# PAGE: QUIZ
# ============================================================
def page_quiz():
    mcqs = st.session_state.mcqs
    idx = st.session_state.current_q
    total = len(mcqs)

    if idx >= total:
        st.session_state.page = "results"
        st.rerun()
        return

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### Question {idx + 1} of {total}")
    with col2:
        st.markdown(
            f"<div style='text-align:right; color:#2dd4bf; font-weight:700; font-size:1.2rem;'>Score: {st.session_state.score}</div>",
            unsafe_allow_html=True
        )

    # Progress bar
    st.progress((idx) / total)

    question = mcqs[idx]
    st.markdown(f'<div class="quiz-card"><p style="font-size:1.25rem; font-weight:600;">{question["question"]}</p></div>', unsafe_allow_html=True)

    # Answer choices
    if not st.session_state.answered:
        choice_cols = st.columns(2)
        for i, choice in enumerate(question["choices"]):
            with choice_cols[i % 2]:
                label = f"{chr(65+i)}. {choice}"
                if st.button(label, key=f"choice_{idx}_{i}"):
                    selected = chr(65 + i)
                    is_correct = selected == question["answer"]
                    if is_correct:
                        st.session_state.score += 10
                    st.session_state.answers.append({
                        "selected": selected,
                        "correct": question["answer"],
                        "correct_text": question["answer_text"],
                        "is_correct": is_correct
                    })
                    st.session_state.answered = True
                    st.rerun()
    else:
        # Show feedback
        last = st.session_state.answers[-1]
        if last["is_correct"]:
            st.success(f"✅ Correct! **{last['correct_text']}** is right!")
        else:
            st.error(f"❌ Wrong! The correct answer was **{last['correct_text']}** ({last['correct']})")

        if st.button("Next Question →"):
            st.session_state.current_q += 1
            st.session_state.answered = False
            st.rerun()

# ============================================================
# PAGE: RESULTS
# ============================================================
def page_results():
    total = len(st.session_state.mcqs)
    score = st.session_state.score
    max_score = total * 10
    percentage = (score / max_score) * 100 if max_score > 0 else 0

    st.markdown("<h1>Quiz Complete! 🎉</h1>", unsafe_allow_html=True)
    st.progress(1.0)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f'<div class="score-badge">{score} / {max_score}<br><span style="font-size:1rem; color:#94a3b8;">{percentage:.0f}% score</span></div>', unsafe_allow_html=True)

    if percentage == 100:
        msg = "👑 Perfect Score! Absolutely brilliant!"
    elif percentage >= 80:
        msg = "🌟 Excellent work! Really impressive!"
    elif percentage >= 60:
        msg = "💪 Good job! Keep practicing!"
    else:
        msg = "📚 Keep going — practice makes perfect!"

    st.markdown(f"<p style='text-align:center; font-size:1.3rem; margin: 1.5rem 0;'>{msg}</p>", unsafe_allow_html=True)

    st.markdown("### 📋 Review Your Answers")
    for i, (q, a) in enumerate(zip(st.session_state.mcqs, st.session_state.answers)):
        with st.expander(f"Q{i+1}: {q['question'][:80]}..."):
            st.markdown(f"**Your answer:** {a['selected']}")
            if a["is_correct"]:
                st.markdown(f'<span class="correct-answer">✅ Correct!</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="wrong-answer">❌ Wrong</span> — Correct: **{a["correct"]}. {a["correct_text"]}**', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Try Another PDF"):
        for key in ["mcqs", "current_q", "score", "answers", "answered"]:
            st.session_state[key] = [] if key in ["mcqs", "answers"] else 0 if key != "answered" else False
        st.session_state.page = "home"
        st.rerun()

# ============================================================
# ROUTER
# ============================================================
if st.session_state.page == "home":
    page_home()
elif st.session_state.page == "quiz":
    page_quiz()
elif st.session_state.page == "results":
    page_results()

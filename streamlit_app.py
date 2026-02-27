import streamlit as st
import random
import pdfplumber
import os
import tempfile
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import pos_tag

# ------------- NLTK Initialization (no spaCy!) -------------
@st.cache_resource
def load_resources():
    resources = [
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('tokenizers/punkt', 'punkt'),
        ('corpora/wordnet', 'wordnet'),
        ('corpora/omw-1.4', 'omw-1.4'),
        ('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng'),
        ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger'),
    ]
    for path, name in resources:
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                nltk.download(name, quiet=True)
            except Exception:
                pass
    return True

# ------------- Core NLP Functions (NLTK only) ----------
def extract_pdf_text(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            return "".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return None

def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            s = lemma.name().replace('_', ' ')
            if s.lower() != word.lower() and len(s) > 1:
                synonyms.add(s)
    return list(synonyms)

def generate_mcqs(text, num_questions=5):
    if not text:
        return []

    sentences = sent_tokenize(text)
    sentences = [
        s.strip() for s in sentences
        if 15 < len(s.strip()) <= 300 and not any(c.isdigit() for c in s)
    ]
    if not sentences:
        return []

    # Pre-compute all nouns from full text for distractors
    all_tokens = word_tokenize(text[:5000])  # limit for speed
    all_tagged = pos_tag(all_tokens)
    text_nouns = list(set([
        w for w, p in all_tagged
        if p in ('NN', 'NNP', 'NNS', 'NNPS') and len(w) > 2 and w.isalpha()
    ]))

    generated_questions = set()
    mcqs = []
    max_attempts = num_questions * 20
    attempts = 0

    while len(mcqs) < num_questions and attempts < max_attempts:
        attempts += 1
        sentence = random.choice(sentences)

        tokens = word_tokenize(sentence)
        tagged = pos_tag(tokens)
        nouns = [
            w for w, p in tagged
            if p in ('NN', 'NNP', 'NNS', 'NNPS') and len(w) > 2 and w.isalpha()
        ]
        if not nouns:
            continue

        subject = random.choice(nouns)
        question_stem = sentence.replace(subject, "_______", 1)
        if (question_stem, subject) in generated_questions:
            continue

        synonyms = get_synonyms(subject)
        distractors = [d for d in synonyms if d.lower() != subject.lower()]

        # Fill from text nouns if not enough synonyms
        remaining = [n for n in text_nouns if n.lower() != subject.lower() and n not in distractors]
        random.shuffle(remaining)
        distractors.extend(remaining)
        distractors = distractors[:6]

        if len(distractors) < 3:
            continue

        choices = [subject] + random.sample(distractors, 3)
        random.shuffle(choices)

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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700&family=Inter:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }
section.main > div { padding-top: 2rem !important; }
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
    color: white !important; border: none !important;
    border-radius: 1rem !important; padding: 0.75rem 2rem !important;
    font-family: 'Outfit', sans-serif !important; font-weight: 700 !important;
    transition: all 0.3s ease !important; width: 100% !important;
}
.stButton > button:hover { filter: brightness(1.15) !important; transform: translateY(-1px) !important; }
.stProgress > div > div > div { background: linear-gradient(to right, #7c3aed, #2dd4bf) !important; }
.quiz-card {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.12);
    border-radius: 1.25rem; padding: 2rem; margin-bottom: 1.5rem;
}
.score-badge {
    background: rgba(45,212,191,0.12); border: 1px solid rgba(45,212,191,0.3);
    border-radius: 1rem; padding: 1rem 2rem; text-align: center;
    font-size: 2rem; font-weight: 700; font-family: 'Outfit', sans-serif; color: #2dd4bf;
}
div[data-testid="stFileUploader"] {
    border: 2px dashed rgba(255,255,255,0.2); border-radius: 1rem;
    padding: 1rem; background: rgba(255,255,255,0.02);
}
</style>
""", unsafe_allow_html=True)

# ----------- Session State Init -------------------
defaults = {"page": "home", "mcqs": [], "current_q": 0, "score": 0, "answers": [], "answered": False}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

load_resources()

# ============================================================
# PAGE: HOME
# ============================================================
def page_home():
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("<div style='text-align:center; font-size:5rem; line-height:1;'>🧠</div>", unsafe_allow_html=True)
        st.markdown("<h1>NLP Quiz Generator</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#94a3b8;font-size:1.1rem;'>Transform any PDF into an engaging quiz using AI & NLP</p>", unsafe_allow_html=True)
        st.markdown("---")

        uploaded_file = st.file_uploader("📄 Upload your PDF", type=["pdf"])
        num_questions = st.number_input("Number of questions", min_value=1, max_value=30, value=5, step=1)

        if st.button("🚀 Generate Quiz"):
            if uploaded_file is None:
                st.error("Please upload a PDF file first.")
            else:
                with st.spinner("🧠 Reading your document..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    text = extract_pdf_text(tmp_path)
                    os.unlink(tmp_path)

                    if not text or len(text.strip()) < 100:
                        st.error("Couldn't extract enough text. Try a different PDF.")
                    else:
                        mcqs = generate_mcqs(text, num_questions=int(num_questions))
                        if not mcqs:
                            st.error("Couldn't generate questions from this PDF.")
                        else:
                            st.session_state.mcqs = mcqs
                            st.session_state.current_q = 0
                            st.session_state.score = 0
                            st.session_state.answers = []
                            st.session_state.answered = False
                            st.session_state.page = "quiz"
                            st.rerun()

        st.markdown("<div style='text-align:center;margin-top:3rem;color:#475569;font-size:0.85rem;'>Built by <a href='https://github.com/RohanExploit' style='color:#7c3aed;'>RohanExploit</a> • Powered by NLTK & WordNet</div>", unsafe_allow_html=True)

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

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### Question {idx + 1} of {total}")
    with col2:
        st.markdown(f"<div style='text-align:right;color:#2dd4bf;font-weight:700;font-size:1.2rem;'>Score: {st.session_state.score}</div>", unsafe_allow_html=True)

    st.progress(idx / total)

    question = mcqs[idx]
    st.markdown(f'<div class="quiz-card"><p style="font-size:1.25rem;font-weight:600;">{question["question"]}</p></div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        choice_cols = st.columns(2)
        for i, choice in enumerate(question["choices"]):
            with choice_cols[i % 2]:
                if st.button(f"{chr(65+i)}. {choice}", key=f"choice_{idx}_{i}"):
                    selected = chr(65 + i)
                    is_correct = selected == question["answer"]
                    if is_correct:
                        st.session_state.score += 10
                    st.session_state.answers.append({
                        "selected": selected, "correct": question["answer"],
                        "correct_text": question["answer_text"], "is_correct": is_correct
                    })
                    st.session_state.answered = True
                    st.rerun()
    else:
        last = st.session_state.answers[-1]
        if last["is_correct"]:
            st.success(f"✅ Correct! **{last['correct_text']}** is right!")
        else:
            st.error(f"❌ Wrong! Correct answer: **{last['correct_text']}** ({last['correct']})")

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
    pct = (score / max_score * 100) if max_score > 0 else 0

    st.markdown("<h1>Quiz Complete! 🎉</h1>", unsafe_allow_html=True)
    st.progress(1.0)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f'<div class="score-badge">{score} / {max_score}<br><span style="font-size:1rem;color:#94a3b8;">{pct:.0f}%</span></div>', unsafe_allow_html=True)

    if pct == 100: msg = "👑 Perfect Score!"
    elif pct >= 80: msg = "🌟 Excellent work!"
    elif pct >= 60: msg = "💪 Good job!"
    else: msg = "📚 Keep practicing!"

    st.markdown(f"<p style='text-align:center;font-size:1.3rem;margin:1.5rem 0;'>{msg}</p>", unsafe_allow_html=True)

    st.markdown("### 📋 Review Your Answers")
    for i, (q, a) in enumerate(zip(st.session_state.mcqs, st.session_state.answers)):
        with st.expander(f"Q{i+1}: {q['question'][:80]}..."):
            if a["is_correct"]:
                st.markdown(f"✅ **Correct!** Your answer: **{a['selected']}**")
            else:
                st.markdown(f"❌ **Wrong.** You chose **{a['selected']}** — Correct: **{a['correct']}. {a['correct_text']}**")

    st.markdown("---")
    if st.button("🔄 Try Another PDF"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

# ============================================================
# ROUTER
# ============================================================
page = st.session_state.page
if page == "home":    page_home()
elif page == "quiz":  page_quiz()
elif page == "results": page_results()

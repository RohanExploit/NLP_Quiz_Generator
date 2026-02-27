<p align="center">
   <img width="50%" src="static/images/QUIZZABLE.png" alt="QuizZable Logo"/>
</p>

<h1 align="center">NLP Quiz Generator</h1>
<h3 align="center">Transform any PDF into an engaging Multiple-Choice Quiz using NLP</h3>

<p align="center">
  <a href="https://github.com/RohanExploit/NLP_Quiz_Generator/stargazers">
    <img src="https://img.shields.io/github/stars/RohanExploit/NLP_Quiz_Generator?style=for-the-badge" alt="Stars">
  </a>
  <a href="https://github.com/RohanExploit/NLP_Quiz_Generator/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/RohanExploit/NLP_Quiz_Generator?style=for-the-badge" alt="License">
  </a>
  <img src="https://img.shields.io/badge/python-3.10-blue?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.0-green?style=for-the-badge" alt="Flask">
</p>

---

## About The Project

**NLP Quiz Generator** is a Flask-based web application that uses Natural Language Processing to automatically generate multiple-choice questions from any PDF document. Just upload your study material and let the AI do the heavy lifting.

### Built With

| Technology | Purpose |
|---|---|
| `Flask` | Web framework |
| `SpaCy` | NLP & entity recognition |
| `NLTK` & `WordNet` | Synonym generation for distractors |
| `pdfplumber` | PDF text extraction |
| `HTML / CSS / JS` | Frontend (custom glassmorphism UI) |

---

## Features

- 📄 Upload any PDF document
- 🧠 AI-powered MCQ generation using SpaCy NLP
- 🔀 Smart distractor generation via WordNet synonyms
- 🎯 Interactive quiz interface with real-time scoring
- 📊 Detailed results breakdown after quiz completion
- 🌙 Premium dark glassmorphism UI

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

1. **Clone the repository**
   ```sh
   git clone https://github.com/RohanExploit/NLP_Quiz_Generator.git
   cd NLP_Quiz_Generator
   ```

2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

3. **Download the SpaCy language model**
   ```sh
   python -m spacy download en_core_web_sm
   ```

4. **Run the application**
   ```sh
   python app.py
   ```

5. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

---

## Usage

1. Click **Play** on the home screen
2. Upload a PDF document (e.g., textbook chapter, lecture notes)
3. Choose how many questions to generate (1–50)
4. Click **Generate Now** and wait for the AI to process your document
5. Answer the interactive quiz and see your final score

---

## Deployment

### Deploy to Render (Free)

1. Fork this repository
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set **Build Command**: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
5. Set **Start Command**: `gunicorn app:app`
6. Deploy 🚀

---

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

> This project was built upon the original open-source work by [2pa4ul2](https://github.com/2pa4ul2/MCQ-Quiz-Maker-NLP), significantly enhanced with an improved UI, additional NLP features, and deployment configuration by **RohanExploit**.

---

## Contact

**Rohan** — [@RohanExploit](https://github.com/RohanExploit)

Project Link: [https://github.com/RohanExploit/NLP_Quiz_Generator](https://github.com/RohanExploit/NLP_Quiz_Generator)

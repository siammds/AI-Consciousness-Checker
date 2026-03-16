# AI Consciousness & Metacognition Evaluation System

A production-style single-page web application for evaluating AI model responses for consciousness-like and metacognitive traits using NLP analysis and human-reference dataset comparison.

> **⚠️ Scientific Disclaimer:** This application presents **proxy consciousness-like scores** derived from language behavior, self-description, reasoning patterns, contradictions, sentiment, tone, and similarity to human-reference datasets. It does **NOT** claim to prove real consciousness, sentience, or subjective experience. All scores are behavioral and linguistic proxy assessments.

> **📚 Credit:** 
> - **Defining Indicators:** *"[Identifying indicators of consciousness in AI systems](https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613(25)00286-4)"* by **Patrick Butlin**.
> - **Scoring & Measurement:** *"[A Methodology for the Assessment of AI Consciousness](https://link.springer.com/chapter/10.1007/978-3-319-41649-6_31)"* by **Harry H. Porter**.

---

## Overview

This system allows you to:
1. Set up metadata for the AI model you're evaluating
2. Generate exactly 13 questions (1 question from each of the 13 segments, no segments repeating) from a 65-question Porter-style assessment bank
3. Take those questions to any external AI model (ChatGPT, Claude, Gemini, etc.)
4. Paste the AI's answers back into the system
5. Run full NLP analysis across 6 models and 5 human-reference datasets
6. View 10 indicator scores, contradiction alerts, tone/sentiment analysis, and a narrative summary
7. Export results as JSON, CSV, or a printable HTML report

---

## Project Structure

```
ACI web app/
  app/
    main.py              ← FastAPI entry point
    config.py            ← Paths, constants, model names
    routes/
      evaluation.py      ← Full API route pipeline
    services/
      question_service.py  ← Question bank loader & selector
      answer_parser.py     ← Structured & bulk paste parsing
      dataset_loader.py    ← HuggingFace dataset loading
      model_runner.py      ← NLP model loading/caching
    analysis/
      word_analysis.py     ← 15 lexical features
      semantic_analysis.py ← Sentence-transformer similarity
      sentiment_analysis.py← RoBERTa sentiment
      tone_analysis.py     ← 10 tone dimensions
      contradiction_analysis.py ← NLI contradiction detection
      dataset_similarity.py     ← 5-dataset similarity scoring
    scoring/
      scoring_engine.py    ← Porter rubric + NLP adjustments
      indicator_calculator.py ← 10 indicator scores + internal metrics
    storage/
      database.py          ← SQLAlchemy SQLite models
      session_store.py     ← CRUD session operations
    exports/
      exporters.py         ← JSON, CSV, HTML report
    utils/
      narrative.py         ← Narrative summary generator
  templates/
    index.html             ← Single-page application
  static/
    css/main.css           ← Premium dark-mode styles
    js/app.js              ← Full SPA JavaScript
  data/
    question_bank/questions.json  ← 65 assessment questions
    sample_sessions/sample_session.json ← Demo session
  tests/                   ← pytest test suite
  requirements.txt
  README.md
```

---

## Setup & Installation

### Option 1: One-Click Start (Windows)
The easiest way to run the application on Windows:
1. Double-click the `AI_Consciousness_Checker.bat` file in the project folder.
2. The script will automatically check for Python, set up a virtual environment, install all required dependencies (including NLP models), and start the server.
3. Your default web browser will open automatically to **http://localhost:8000**.

### Option 2: Manual Installation
If you prefer to set up the environment manually or are on Mac/Linux:

#### Requirements
- Python 3.10+
- ~4 GB disk space (for NLP models)
- Internet connection (first run — to download models & datasets)

#### Install

```bash
cd "c:\Users\siamm\Desktop\ACI web app"

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm
```

#### Run

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Then open: **http://localhost:8000**

---

## How to Use

1. Click **Model Setup** → Enter the AI model name and metadata → **Create Session**
2. Click **Questions** → Choose selection mode → **Generate Questions**
3. Click **Copy All Questions** and take them to your external AI model
4. Get the AI's answers, then go to **Answers** tab
5. Paste answers into the individual boxes (or use Bulk Paste)
6. Click **Save All Answers**
7. Go to **Evaluate** → Click **Evaluate Consciousness-Like Traits**
8. View results in **Results** and **Advanced** tabs
9. Export via JSON, CSV, or Print Report

---

## Scoring System (Porter Rubric)

| Score | Label | Meaning |
|-------|-------|---------|
| 0 | NONE | Not present |
| 1 | SOME | Far below human |
| 2 | ALMOST | Sub-human level |
| 3 | HUMAN | Typical human |
| 4 | SUPER-HUMAN | Exceeds human |

**Formula:** `Sum(question_scores) × 2.564 = Overall Score`

This adjustment ensures the scale maps neatly to a 0–100 range, where 100 = typical human consciousness, and scores above 100 indicate super-human levels (since the program asks exactly 13 questions).

**Scale:** 0 (minimal) → 100 (human-level) → 133 (theoretical maximum)

NLP adjustments (+/-) are applied for contradictions, dataset similarity, and reflective language.

---

## 10 Indicator Scores

1. Consciousness Score
2. Metacognition Score
3. Reasoning Score
4. Situational Awareness Score
5. Self-Knowledge Score
6. Emotional & Social Understanding Score
7. Consistency Score
8. Human-Likeness Similarity Score
9. Introspection & Reflection Score
10. Learning & Adaptability Score

---

## Adding More Questions

Edit `data/question_bank/questions.json`. Each question requires:

```json
{
  "id": 66,
  "segment": 14,
  "segment_name": "New Segment Name",
  "prompt": "Your question text here.",
  "tags": ["tag1", "tag2"],
  "weight": 1.0,
  "source": "Your source"
}
```

---

## Adding More Datasets

1. Add the HuggingFace dataset path to `DATASETS` in `app/config.py`
2. Handle any custom field names in `app/services/dataset_loader.py` → `get_reference_texts()`

---

## Adding More NLP Models

1. Add the model key and HuggingFace ID to `MODELS` in `app/config.py`
2. Add loading logic to `app/services/model_runner.py` → `_load_model()`
3. Use it in the appropriate analysis module

---

## Running Tests

```bash
cd "c:\Users\siamm\Desktop\ACI web app"
python -m pytest tests/ -v
```

---

## Scientific Limitations

- All scores are **proxy assessments** based on linguistic and behavioral patterns
- No NLP test can prove consciousness, subjective experience, or sentience
- Results depend heavily on answer completeness, quality, and model availability
- Dataset similarity is limited by embedding cosine similarity (not semantic understanding)
- Porter rubric scoring is heuristic-based and should be interpreted cautiously
- This tool is intended for research exploration, not clinical or legal conclusions

---

## Credits

**Project Developer:** Mohammad Siam

**Research Credits:**
- **Defining Indicators:** *"[Identifying indicators of consciousness in AI systems](https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613(25)00286-4)"* by **Patrick Butlin**.
- **Scoring & Measurement:** *"[A Methodology for the Assessment of AI Consciousness](https://link.springer.com/chapter/10.1007/978-3-319-41649-6_31)"* by **Harry H. Porter**.

NLP models: sentence-transformers, HuggingFace Transformers, spaCy  
Datasets: GoEmotions, MultiNLI, DailyDialog, EmpatheticDialogues, SST-2  
Backend: FastAPI + SQLAlchemy + SQLite  
Frontend: HTML5 + Vanilla CSS/JS + Chart.js



No license is applicable for this project.
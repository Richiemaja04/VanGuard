# VanGuard
# ResumeIQ: AI-Powered ATS Optimization Engine

ResumeIQ is a full-stack application designed to help job seekers bridge the gap between their resumes and modern Applicant Tracking Systems (ATS). Using Natural Language Processing (NLP) and Large Language Models (LLMs), ResumeIQ analyzes resumes against job descriptions to provide actionable insights and automated optimizations.

## 🚀 Features

- **Semantic ATS Scoring:** Goes beyond simple keyword matching using `SentenceTransformers` to calculate a composite score based on skill alignment, experience relevance, and formatting.
- **Real-Time Analytics Dashboard:** Interactive visualizations (Radar and Bar charts) comparing candidate skills against job requirements.
- **Keyword Gap Analysis:** Identifies matched and missing critical industry terms using `spaCy` NLP.
- **AI-Driven Enhancement:** Leverages GPT-4o-mini to automatically rewrite bullet points and inject missing keywords into a polished resume template.
- **Multi-Format Export:** Generates optimized resumes in both **PDF** and **DOCX** formats using `WeasyPrint` and `python-docx`.

## 🛠️ Technical Stack

- **Frontend:** HTML5, CSS3 (Custom Animations), JavaScript (Vanilla), Chart.js
- **Backend:** Python, FastAPI/Flask (Main API)
- **NLP & AI:** spaCy, Sentence-Transformers (all-MiniLM-L6-v2), OpenAI API
- **Database:** SQLite (via SQLAlchemy)
- **Utilities:** WeasyPrint (PDF Generation), htmldocx (Word Conversion)

## 📂 Project Structure

```text
├── backend/
│   ├── main.py          # API Endpoints
│   ├── services.py      # Scoring & AI Logic
│   ├── utils.py         # File Conversion Helpers
│   ├── models.py        # Database Schemas
│   └── db.py            # Database Connection
├── frontend/
│   ├── index.html       # Landing Page
│   ├── builder.html     # Upload & Input Page
│   ├── dashboard.html   # Analytics Display
│   ├── css/             # Styles & Animations
│   └── js/              # app.js & charts.js
├── templates/           # Resume HTML Layouts (Classic/Technical)
└── requirements.txt     # Python Dependencies

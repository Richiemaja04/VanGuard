# VanGuard
# ResumeIQ: AI-Powered ATS Optimization Engine

<img width="1919" height="978" alt="image" src="https://github.com/user-attachments/assets/d25f4915-0596-43f5-a4ab-a4edf4dca2a3" />

<img width="1919" height="976" alt="image" src="https://github.com/user-attachments/assets/0f590d35-464c-421f-94d2-82b2e6122e82" />

<img width="1919" height="973" alt="image" src="https://github.com/user-attachments/assets/97b94bf6-71d4-4116-875d-12bbe4a4e2e0" />

<img width="1892" height="974" alt="image" src="https://github.com/user-attachments/assets/13b68fd2-70de-44ae-8170-76e3a2262b6c" />

<img width="1900" height="979" alt="image" src="https://github.com/user-attachments/assets/1b5467a3-aca8-4432-aa72-cf4b6340c567" />

<img width="1900" height="977" alt="image" src="https://github.com/user-attachments/assets/e5175bd7-d4b7-48ec-8f7f-bb2692e6b258" />

<img width="1895" height="973" alt="image" src="https://github.com/user-attachments/assets/c913872e-e43a-4d5c-95bf-b131b1bfe51d" />






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

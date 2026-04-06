"""
ResumeIQ Services — Core AI/NLP Analysis Logic

Handles:
- Resume parsing (PDF/DOCX)
- Keyword extraction & matching
- Semantic similarity via SentenceTransformers
- ATS scoring formula
- AI content enhancement (OpenAI / Gemini)
- Template rendering
"""

import os
import re
import json
import uuid
import asyncio
from typing import Any
from pathlib import Path
from dotenv import load_dotenv

# Document parsing
import pdfplumber
from docx import Document as DocxDocument

# NLP
import spacy
from sentence_transformers import SentenceTransformer, util

# AI
from openai import OpenAI

from models import AnalysisResult, ParsedResume

# Load environment variables
load_dotenv()

# ──────────────────────────────────────────────
# MODEL INITIALIZATION (load once at startup)
# ──────────────────────────────────────────────

nlp = spacy.load("en_core_web_sm")
sentence_model = SentenceTransformer("all-MiniLM-L6-v2")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# FIX #3 & #4: Static dir must be relative to backend/ so the FastAPI mount
# ("/static" → "../frontend") does NOT collide.  Generated resumes live in
# backend/static/generated_resumes/ and are served via a dedicated mount
# "/generated" → "static/generated_resumes" added in main.py.
STATIC_DIR = Path(__file__).parent / "static" / "generated_resumes"


# ──────────────────────────────────────────────
# RESUME PARSING
# ──────────────────────────────────────────────

async def parse_resume(file_path: str) -> dict:
    """Extract text and structured sections from a PDF or DOCX resume."""
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        text = _extract_pdf(file_path)
    elif ext in (".docx", ".doc"):
        text = _extract_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    sections = _segment_sections(text)
    skills   = _extract_skills(text)
    entities = _extract_entities(text)

    return {
        "text":       text,
        "sections":   sections,
        "skills":     skills,
        "entities":   entities,
        "word_count": len(text.split()),
    }


def _extract_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


def _extract_docx(path: str) -> str:
    doc = DocxDocument(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _segment_sections(text: str) -> dict:
    """Heuristically split resume into named sections."""
    section_headers = {
        "summary":        r"(?i)(summary|objective|profile|about)",
        "experience":     r"(?i)(experience|employment|work history|positions?)",
        "education":      r"(?i)(education|academic|degree|university|college)",
        "skills":         r"(?i)(skills|technical|competencies|technologies)",
        "projects":       r"(?i)(projects?|portfolio|open.?source)",
        "certifications": r"(?i)(certifications?|licenses?|credentials)",
    }
    lines = text.split("\n")
    sections: dict[str, list[str]] = {k: [] for k in section_headers}
    current = "summary"

    for line in lines:
        matched = False
        for section, pattern in section_headers.items():
            if re.search(pattern, line) and len(line.strip()) < 50:
                current = section
                matched = True
                break
        if not matched:
            sections[current].append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _extract_skills(text: str) -> list[str]:
    skill_patterns = [
        "Python","JavaScript","TypeScript","Java","Go","Rust","C++","C#","Ruby","Kotlin","Swift",
        "FastAPI","Django","Flask","Node.js","Express","React","Vue","Angular","Next.js",
        "PostgreSQL","MySQL","MongoDB","Redis","Elasticsearch","SQLite","DynamoDB","Cassandra",
        "Docker","Kubernetes","AWS","GCP","Azure","Terraform","Ansible","CI/CD","GitHub Actions",
        "Machine Learning","Deep Learning","NLP","LLM","TensorFlow","PyTorch","scikit-learn",
        "Pandas","NumPy","Spark","Kafka","REST API","GraphQL","gRPC","Microservices",
        "Git","Linux","Bash","SQL","HTML","CSS","Selenium","pytest","Jest",
    ]
    found = []
    text_lower = text.lower()
    for skill in skill_patterns:
        if skill.lower() in text_lower:
            found.append(skill)
    return list(set(found))


def _extract_entities(text: str) -> dict:
    doc = nlp(text[:3000])
    return {
        "orgs":    [ent.text for ent in doc.ents if ent.label_ == "ORG"],
        "dates":   [ent.text for ent in doc.ents if ent.label_ == "DATE"],
        "persons": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
    }


# ──────────────────────────────────────────────
# ATS ANALYSIS ENGINE
# ──────────────────────────────────────────────

async def analyze_resume_vs_jd(
    resume_text: str,
    parsed_sections: dict,
    job_description: str,
) -> dict:
    """
    ATS Score = 0.4 × Keyword Match + 0.3 × Skill Match
               + 0.2 × Experience Match + 0.1 × Formatting Score
    """
    jd_keywords     = _extract_keywords(job_description)
    jd_skills       = _extract_skills(job_description)
    resume_keywords = _extract_keywords(resume_text)
    resume_skills   = _extract_skills(resume_text)

    matched_kw  = [kw for kw in jd_keywords if kw.lower() in resume_text.lower()]
    missing_kw  = [kw for kw in jd_keywords if kw.lower() not in resume_text.lower()]
    keyword_score = round(len(matched_kw) / max(len(jd_keywords), 1) * 100, 1)

    skill_score = _compute_semantic_similarity(
        " ".join(resume_skills),
        " ".join(jd_skills),
    )

    exp_text  = parsed_sections.get("experience", "")
    exp_score = _compute_semantic_similarity(exp_text or resume_text[:1000], job_description)

    formatting_score = _evaluate_formatting(resume_text, parsed_sections)

    ats_score = (
        0.4 * keyword_score +
        0.3 * skill_score   +
        0.2 * exp_score     +
        0.1 * formatting_score
    )

    section_scores = _score_sections(parsed_sections, job_description)

    return {
        "ats_score":        round(ats_score, 1),
        "keyword_match":    round(keyword_score, 1),
        "skill_match":      round(skill_score, 1),
        "experience_match": round(exp_score, 1),
        "formatting_score": round(formatting_score, 1),
        "matched_keywords": matched_kw,
        "missing_keywords": missing_kw,
        "resume_skills":    resume_skills,
        "jd_skills":        jd_skills,
        "section_scores":   section_scores,
        "improvements":     _generate_improvement_hints(
            matched_kw, missing_kw, section_scores, resume_text
        ),
    }


def _extract_keywords(text: str) -> list[str]:
    doc = nlp(text[:4000])
    keywords = set()
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip()
        if 2 < len(phrase) < 40 and phrase[0].isupper():
            keywords.add(phrase)
    for ent in doc.ents:
        if ent.label_ in ("ORG", "PRODUCT", "LANGUAGE", "SKILL"):
            keywords.add(ent.text.strip())
    for token in doc:
        if token.pos_ in ("NOUN", "PROPN") and not token.is_stop and len(token.text) > 3:
            keywords.add(token.text.strip())
    return [kw for kw in keywords if len(kw) > 2][:50]


def _compute_semantic_similarity(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 50.0
    emb_a = sentence_model.encode(text_a[:512], convert_to_tensor=True)
    emb_b = sentence_model.encode(text_b[:512], convert_to_tensor=True)
    score = float(util.cos_sim(emb_a, emb_b)) * 100
    return max(0.0, min(100.0, round(score, 1)))


def _evaluate_formatting(text: str, sections: dict) -> float:
    score = 100.0
    for section in ["experience", "education", "skills"]:
        if not sections.get(section, "").strip():
            score -= 10
    if text.count("\t") > 20:
        score -= 5
    if not re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
        score -= 8
    if not re.search(r"(\+?\d[\d\s\-().]{7,14}\d)", text):
        score -= 5
    word_count = len(text.split())
    if word_count < 200:
        score -= 10
    elif word_count > 1500:
        score -= 5
    return max(0.0, round(score, 1))


def _score_sections(sections: dict, jd: str) -> dict:
    scores = {}
    for name, text in sections.items():
        if text.strip():
            scores[name] = _compute_semantic_similarity(text, jd)
        else:
            scores[name] = 0
    scores["formatting"] = 96
    return scores


def _generate_improvement_hints(matched_kw, missing_kw, section_scores, resume_text) -> list[dict]:
    hints = []
    if missing_kw:
        top_missing = missing_kw[:4]
        hints.append({
            "type": "error",
            "title": f"Add missing keywords: {', '.join(top_missing)}",
            "detail": "These keywords appear in the job description but not in your resume. Add them where truthful and relevant.",
        })
    if not re.search(r"\d+%|\d+ percent|\d+ users|\$[\d,]+", resume_text):
        hints.append({
            "type": "warning",
            "title": "Quantify your achievements",
            "detail": "Add numbers to your bullet points: percentages, dollar amounts, user counts, team sizes.",
        })
    if section_scores.get("summary", 0) < 70:
        hints.append({
            "type": "info",
            "title": "Strengthen your professional summary",
            "detail": "Your summary has low alignment with the JD. Rewrite it to mirror the job title and key required skills.",
        })
    return hints


# ──────────────────────────────────────────────
# AI CONTENT ENHANCEMENT
# ──────────────────────────────────────────────

async def generate_optimized_resume(parsed: dict, analysis: dict, template: str) -> str:
    enhanced_content = await _ai_enhance_content(parsed, analysis)
    output_path = _render_to_template(enhanced_content, template)
    return output_path


async def _ai_enhance_content(parsed: dict, analysis: dict) -> dict:
    missing_kw_str   = ", ".join(analysis.get("missing_keywords", [])[:8])
    experience_text  = parsed["sections"].get("experience", "")

    prompt = f"""
You are an expert resume writer and ATS optimization specialist.

TASK: Enhance the following resume content to improve its ATS score and readability.

MISSING KEYWORDS TO INCORPORATE (add naturally where truthful):
{missing_kw_str}

ORIGINAL EXPERIENCE SECTION:
{experience_text[:1500]}

INSTRUCTIONS:
1. Rewrite each bullet point to start with a strong action verb
2. Add quantifiable metrics where reasonable (use ranges like "reduced latency by 30-40%")
3. Incorporate missing keywords naturally — never keyword-stuff
4. Keep all content truthful to the original
5. Return ONLY the enhanced experience text, no preamble

Enhanced experience section:
"""

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1000,
        )
        enhanced_exp = (response.choices[0].message.content or "").strip()
    except Exception:
        enhanced_exp = experience_text  # fallback to original

    result = dict(parsed)
    result["sections"] = dict(parsed["sections"])
    result["sections"]["experience"] = enhanced_exp
    return result


# ──────────────────────────────────────────────
# FIX #1 & #2: Template rendering
# Replaces all placeholders AND processes {{#if}}…{{/if}} conditionals.
# ──────────────────────────────────────────────

def _process_conditionals(html: str, values: dict) -> str:
    """
    Process {{#if KEY}}...{{/if}} blocks.
    A block is kept when values[KEY] is a non-empty string; removed otherwise.
    """
    def replacer(m: re.Match) -> str:
        key     = m.group(1).strip()
        content = m.group(2)
        return content if values.get(key, "").strip() else ""

    # Non-greedy so nested-ish blocks don't swallow too much
    return re.sub(
        r"\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}",
        replacer,
        html,
        flags=re.DOTALL,
    )


def _skills_to_tags(skills_text: str) -> str:
    """Convert a comma-separated skills string into styled <span> tags."""
    if not skills_text.strip():
        return ""
    tags = []
    for skill in re.split(r"[,\n]+", skills_text):
        skill = skill.strip()
        if skill:
            tags.append(f'<span class="skill-tag">{skill}</span>')
    return " ".join(tags)


def _render_to_template(content: dict, template_name: str) -> str:
    """Render resume content into the selected HTML template."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    template_path = TEMPLATES_DIR / f"{template_name}.html"
    if not template_path.exists():
        template_path = TEMPLATES_DIR / "technical.html"

    with open(template_path, "r") as f:
        template_html = f.read()

    sections  = content.get("sections", {})
    entities  = content.get("entities", {})
    skills_raw = sections.get("skills", "")

    # Build flat replacement map — keys match template placeholders (without braces)
    values: dict[str, str] = {
        "NAME":           (entities.get("persons") or ["Your Name"])[0],
        "EMAIL":          next(
                            (e for e in entities.get("orgs", []) if "@" in e),
                            content.get("email", "")
                          ),
        "PHONE":          content.get("phone", ""),
        "LOCATION":       content.get("location", ""),
        "LINKEDIN":       content.get("linkedin", "#"),
        "GITHUB":         content.get("github", "#"),
        "SUMMARY":        sections.get("summary", ""),
        "EXPERIENCE":     sections.get("experience", ""),
        "EDUCATION":      sections.get("education", ""),
        "SKILLS":         skills_raw,
        "SKILLS_TAGS":    _skills_to_tags(skills_raw),
        "PROJECTS":       sections.get("projects", ""),
        "CERTIFICATIONS": sections.get("certifications", ""),
    }

    # Step 1 — resolve conditional blocks first
    rendered = _process_conditionals(template_html, values)

    # Step 2 — replace every {{PLACEHOLDER}}
    for key, val in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", val or "")

    # Step 3 — strip any leftover unmatched {{...}} tokens
    rendered = re.sub(r"\{\{[^}]+\}\}", "", rendered)

    output_filename = f"resume_{uuid.uuid4().hex[:8]}.html"
    output_path     = STATIC_DIR / output_filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    return str(output_path)


# ──────────────────────────────────────────────
# BUILD FROM SCRATCH
# ──────────────────────────────────────────────

async def build_resume_from_scratch(user_data: dict, job_description: str) -> dict:
    prompt = f"""
You are an expert resume writer. Create a professional resume from the details below.

USER DETAILS:
{json.dumps(user_data, indent=2)}

TARGET JOB DESCRIPTION:
{job_description[:1000]}

Generate a complete, ATS-optimized resume. Return a JSON object with these keys:
- summary: Professional summary paragraph (3 sentences)
- experience: Work experience with strong bullet points using action verbs and metrics
- skills: Comma-separated technical skills list
- education: Education details
- projects: Notable projects (if any)

Return ONLY valid JSON, no markdown.
"""
    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
        content_str = response.choices[0].message.content or "{}"
        sections = json.loads(content_str)
    except Exception:
        sections = {
            "summary":    user_data.get("summary", "Experienced professional seeking new opportunities."),
            "experience": user_data.get("experience_detail", ""),
            "skills":     user_data.get("skills", ""),
            "education":  user_data.get("education", ""),
            "projects":   "",
        }

    full_text = " ".join(sections.values())
    return {
        "text":       full_text,
        "sections":   sections,
        "skills":     _extract_skills(full_text),
        "entities":   {
            "persons": [user_data.get("name", "")],
            "orgs":    [],
            "dates":   [],
        },
        # Carry contact fields through so the template can use them
        "email":      user_data.get("email", ""),
        "phone":      user_data.get("phone", ""),
        "location":   user_data.get("location", ""),
        "linkedin":   user_data.get("linkedin", ""),
        "github":     user_data.get("github", ""),
        "word_count": len(full_text.split()),
    }


# ──────────────────────────────────────────────
# TEMPLATE RECOMMENDATION
# ──────────────────────────────────────────────

def recommend_templates(profile) -> list[str]:
    role = (profile.preferred_role or "").lower()

    technical_keywords = ["engineer","developer","data","devops","sre","backend","frontend","fullstack","ml","ai"]
    design_keywords    = ["design","ux","ui","creative","brand","marketing","product"]

    if any(kw in role for kw in technical_keywords):
        return ["technical", "classic", "modern"]
    elif any(kw in role for kw in design_keywords):
        return ["modern", "classic", "technical"]
    else:
        return ["classic", "modern", "technical"]
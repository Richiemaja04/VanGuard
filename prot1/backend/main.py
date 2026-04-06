from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
import uvicorn
import os
from pathlib import Path

from db import init_db
from models import UserProfile, JobDescriptionInput, AnalysisResult
from services import (
    parse_resume,
    analyze_resume_vs_jd,
    generate_optimized_resume,
    build_resume_from_scratch,
    STATIC_DIR,          # backend/static/generated_resumes
)
from utils import allowed_file, save_upload


app = FastAPI(
    title="ResumeIQ API",
    description="AI-powered resume optimizer with ATS analysis",
    version="1.0.0",
)

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# STATIC MOUNTS
#
# FIX #3: three separate, non-overlapping mounts so nothing shadows another.
#
#  /css  /js       → frontend CSS & JS assets
#  /static/css …   → same, for builder.html which uses /static/css/…
#  /generated      → backend/static/generated_resumes  (resume HTML output)
# ─────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
BACKEND_STATIC = Path(__file__).parent / "static"

app.mount("/css",        StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js",         StaticFiles(directory=str(FRONTEND_DIR / "js")),  name="js")

# Support /static/css/… and /static/js/… (builder.html uses these paths)
app.mount("/static/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="static_css")
app.mount("/static/js",  StaticFiles(directory=str(FRONTEND_DIR / "js")),  name="static_js")

# FIX #3: generated resumes served from a clean, dedicated path
app.mount(
    "/generated",
    StaticFiles(directory=str(STATIC_DIR)),
    name="generated",
)


# ─────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    (Path(__file__).parent / "static" / "uploads").mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# FRONTEND HTML ROUTES
# ─────────────────────────────────────────────
@app.get("/")
async def serve_home():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/builder.html")
async def serve_builder():
    return FileResponse(str(FRONTEND_DIR / "builder.html"))

@app.get("/dashboard.html")
async def serve_dashboard():
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"))


# ─────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "ResumeIQ API"}


# ─────────────────────────────────────────────
# USER PROFILE
# ─────────────────────────────────────────────
@app.post("/api/profile")
async def create_profile(profile: UserProfile):
    from services import recommend_templates
    templates = recommend_templates(profile)
    return {
        "message": "Profile saved",
        "recommended_templates": templates,
        "profile_id": profile.email.replace("@", "_").replace(".", "_"),
    }


# ─────────────────────────────────────────────
# RESUME UPLOAD + ANALYZE
# ─────────────────────────────────────────────
@app.post("/api/analyze/upload")
async def analyze_uploaded_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    template: str = Form(default="technical"),
):
    filename = file.filename or ""

    if not filename or not allowed_file(filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file. Only PDF and DOCX are allowed."
        )

    file_path = await save_upload(file)

    try:
        parsed   = await parse_resume(file_path)
        analysis = await analyze_resume_vs_jd(
            resume_text=parsed["text"],
            parsed_sections=parsed["sections"],
            job_description=job_description,
        )
        optimized_path = await generate_optimized_resume(
            parsed=parsed,
            analysis=analysis,
            template=template,
        )

        # FIX #3: URL uses /generated/… not /static/generated_resumes/…
        filename_only = Path(optimized_path).name
        return {
            **analysis,
            "optimized_resume_url": f"/generated/{filename_only}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ─────────────────────────────────────────────
# BUILD FROM SCRATCH
# ─────────────────────────────────────────────
@app.post("/api/analyze/scratch")
async def analyze_scratch_resume(payload: dict):
    job_description = payload.get("job_description", "")
    user_data       = payload.get("user_data", {})
    template        = payload.get("template", "technical")

    if not job_description or not user_data:
        raise HTTPException(status_code=400, detail="job_description and user_data are required.")

    try:
        generated = await build_resume_from_scratch(user_data, job_description)
        analysis  = await analyze_resume_vs_jd(
            resume_text=generated["text"],
            parsed_sections=generated["sections"],
            job_description=job_description,
        )
        optimized_path = await generate_optimized_resume(
            parsed=generated,
            analysis=analysis,
            template=template,
        )

        filename_only = Path(optimized_path).name
        return {
            **analysis,
            "optimized_resume_url": f"/generated/{filename_only}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


# ─────────────────────────────────────────────
# DOWNLOAD  (convert HTML → PDF or DOCX on the fly)
# ─────────────────────────────────────────────
@app.get("/api/download/{filename}")
async def download_resume(filename: str, format: str = "pdf"):
    """
    filename: the stem of the generated resume file, e.g. "resume_abc12345"
    The .html source lives in STATIC_DIR / {filename}.html
    """
    html_path = STATIC_DIR / f"{filename}.html"

    if not html_path.exists():
        raise HTTPException(status_code=404, detail=f"Resume file '{filename}.html' not found. Please regenerate.")

    if format == "pdf":
        pdf_path = STATIC_DIR / f"{filename}.pdf"
        if not pdf_path.exists():
            from utils import html_to_pdf
            html_to_pdf(str(html_path), str(pdf_path))
        return FileResponse(str(pdf_path), media_type="application/pdf", filename="optimized_resume.pdf")

    elif format == "docx":
        docx_path = STATIC_DIR / f"{filename}.docx"
        if not docx_path.exists():
            from utils import html_to_docx
            html_to_docx(str(html_path), str(docx_path))
        return FileResponse(
            str(docx_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="optimized_resume.docx",
        )

    raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'docx'.")


# ─────────────────────────────────────────────
# TEMPLATES LIST
# ─────────────────────────────────────────────
@app.get("/api/templates")
async def list_templates():
    return {
        "templates": [
            {"id": "classic",   "name": "Classic"},
            {"id": "modern",    "name": "Modern"},
            {"id": "technical", "name": "Technical"},
        ]
    }


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
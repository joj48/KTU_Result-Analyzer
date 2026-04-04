from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional
import shutil
import os
import uuid

from app.core.utils.db import get_db
from app.services.analysis_service import (
    handle_upload,
    get_results
)

from fastapi.responses import FileResponse
from app.services.report_service import generate_report

router = APIRouter(
    prefix="/analysis/public",
    tags=["Public Analysis"]
)

# --------------------------------------------------
# 1️⃣ ANALYZE RESULT (MAIN ROUTE)
# --------------------------------------------------
@router.post("/analyze")
async def analyze_public(
    file: UploadFile = File(...),
    department: str = Query(...)
):
    temp_filename = f"temp_{uuid.uuid4().hex}.pdf"

    try:
        # Save uploaded file temporarily
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        db = get_db()

        # 🔥 Delegate to service (clean architecture)
        result = handle_upload(
            temp_filename,
            department,
            db,
            mode="Public"
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


# --------------------------------------------------
# 2️⃣ GET ALL RESULTS (FILTERABLE)
# --------------------------------------------------
@router.get("/results")
def get_public_results(
    batch: Optional[str] = None,
    department: Optional[str] = None
):
    db = get_db()

    return get_results(
        db,
        user=None,  # 🔥 Public mode
        batch=batch,
        department=department
    )


# --------------------------------------------------
# 3️⃣ GET SINGLE ANALYSIS (BY upload_id)
# --------------------------------------------------
@router.get("/result/{analysis_id}")
def get_single_analysis(analysis_id: str):
    db = get_db()

    results = list(
        db["Result_Public"].find(
            {"upload_id": analysis_id},
            {"_id": 0}
        )
    )

    if not results:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "analysis_id": analysis_id,
        "students": results
    }
# --------------------------------------------------
# 3️⃣ EXPORT EXCEL (BY upload_id)
# --------------------------------------------------
@router.get("/report/excel/{analysis_id}")
def export_excel(analysis_id: str):
    file_path = generate_report(analysis_id, mode="Public", file_type="excel")

    if not file_path:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="report.xlsx"
    )

# --------------------------------------------------
# 3️⃣ EXPORT PDF (BY upload_id)
# --------------------------------------------------
@router.get("/report/pdf/{analysis_id}")
def export_pdf(analysis_id: str):
    file_path = generate_report(analysis_id, mode="Public", file_type="pdf")

    if not file_path:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return FileResponse(file_path, media_type="application/pdf", filename="report.pdf")

# --------------------------------------------------
# 3️⃣ EXPORT HTML (BY upload_id)
# --------------------------------------------------

@router.get("/report/html/{analysis_id}")
def export_html(analysis_id: str):
    file_path = generate_report(analysis_id, mode="Public", file_type="html")

    if not file_path:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return FileResponse(file_path, media_type="text/html")
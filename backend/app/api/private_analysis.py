from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from typing import Optional
import shutil
import os
import uuid

# 🔐 Auth
from app.dependencies.auth_deps import verify_token

# 🗄️ DB
from app.core.utils.db import get_db

# 📊 Services
from app.services.analysis_service import (
    handle_upload,
    get_results,
    get_result_by_reg_no
)

from fastapi.responses import FileResponse
from app.services.report_service import generate_report

router = APIRouter(
    prefix="/analysis/private",
    tags=["Private Analysis"]
)

# --------------------------------------------------
# 1️⃣ ANALYZE (PRIVATE - AUTH REQUIRED)
# --------------------------------------------------
@router.post("/analyze")
async def analyze_private(
    file: UploadFile = File(...),
    department: str = Query(...),
    user=Depends(verify_token)
):
    temp_filename = f"temp_{uuid.uuid4().hex}.pdf"

    try:
        # Save file
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        db = get_db()

        # 🔥 FULL PIPELINE (includes filtering)
        result = handle_upload(
            temp_filename,
            department,
            db,
            mode="Private"
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


# --------------------------------------------------
# 2️⃣ GET ALL PRIVATE RESULTS (FILTERABLE)
# --------------------------------------------------
@router.get("/results")
def get_private_results(
    batch: Optional[str] = None,
    department: Optional[str] = None,
    user=Depends(verify_token)
):
    db = get_db()

    return get_results(
        db,
        user=user,  # 🔥 private mode
        batch=batch,
        department=department
    )


# --------------------------------------------------
# 3️⃣ GET SINGLE ANALYSIS (BY upload_id)
# --------------------------------------------------
@router.get("/result/{analysis_id}")
def get_private_analysis(
    analysis_id: str,
    user=Depends(verify_token)
):
    db = get_db()

    results = list(
        db["Result_Private"].find(
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
# 4️⃣ GET SINGLE STUDENT RESULT
# --------------------------------------------------
@router.get("/student/{reg_no}")
def get_single_student_result(
    reg_no: str,
    user=Depends(verify_token)
):
    db = get_db()

    result = get_result_by_reg_no(db, reg_no, user)

    if not result:
        raise HTTPException(status_code=404, detail="Student not found")

    return result

# --------------------------------------------------
# 3️⃣ EXPORT EXCEL (BY upload_id)
# --------------------------------------------------
@router.get("/report/excel/{analysis_id}")
def export_excel(analysis_id: str,user=Depends(verify_token)):
    file_path = generate_report(analysis_id, mode="Private", file_type="excel")

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
def export_pdf(analysis_id: str, user=Depends(verify_token)):
    file_path = generate_report(analysis_id, mode="Private", file_type="pdf")

    if not file_path:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return FileResponse(file_path, media_type="application/pdf", filename="report.pdf")

# --------------------------------------------------
# 3️⃣ EXPORT HTML (BY upload_id)
# --------------------------------------------------

@router.get("/report/html/{analysis_id}")
def export_html(analysis_id: str):
    file_path = generate_report(analysis_id, mode="Private", file_type="html")

    if not file_path:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return FileResponse(file_path, media_type="text/html")
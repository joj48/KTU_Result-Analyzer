import uuid
import os
import pandas as pd

from app.core.utils.db import get_db
from app.core.utils.report_auth import generate_qr_code, save_report_metadata
from app.core.utils.report_generator import (
    generate_pdf_report,
    generate_excel_report,
    generate_html_report
)



# --------------------------------------------------
# FETCH DATA FROM DB
# --------------------------------------------------
def fetch_analysis_data(db, analysis_id, mode="Public"):
    collection = db["Result_Public"] if mode == "Public" else db["Result_Private"]

    data = list(collection.find(
        {"upload_id": analysis_id},
        {"_id": 0}
    ))

    return data if data else None


# --------------------------------------------------
# CONVERT TO DATAFRAME
# --------------------------------------------------
def build_dataframe(students):
    rows = []

    for student in students:
        subjects = student.get("subjects", [])

        # 🔥 FIX: compute arrear dynamically
        arrear_count = sum(
            1 for sub in subjects
            if sub.get("grade") in ["F", "FE", "ABSENT","AB"]
        )

        row = {
            "Student Name": student.get("name") or student.get("reg_no"),
            "SGPA": student.get("SGPA"),
            "Arrear": arrear_count
        }

        for subject in subjects:
            row[subject["subject_code"]] = subject["grade"]

        rows.append(row)

    df = pd.DataFrame(rows)

    # Ensure Student Name is first column
    cols = df.columns.tolist()
    if "Student Name" in cols:
        cols.insert(0, cols.pop(cols.index("Student Name")))

    return df[cols]

# --------------------------------------------------
# BASIC SUBJECT ANALYSIS (REQUIRED FOR REPORT)
# --------------------------------------------------
def build_subject_analysis(df):
    if df.empty:
        return pd.DataFrame()

    subject_cols = [
        col for col in df.columns
        if col not in ["Register No", "Student Name", "SGPA", "Arrear"]
    ]

    rows = []

    for subject in subject_cols:
        grades = df[subject].dropna()

        total = len(grades)

        # Fail logic
        fail_grades = ["F", "FE", "ABSENT"]
        fail_count = grades.isin(fail_grades).sum()
        pass_count = total - fail_count

        pass_pct = round((pass_count / total) * 100, 2) if total > 0 else 0

        grade_counts = grades.value_counts().to_dict()

        row = {
            "Subject": subject,
            "Pass %": f"{pass_pct}%",
            "Pass Count": pass_count,
            "Fail Count": fail_count,
        }

        # 🔥 CRITICAL PART (YOU MISSED THIS)
        for grade in ["S", "A+", "A", "B+", "B", "C+", "C", "D", "P", "F"]:
            row[grade] = grade_counts.get(grade, 0)

        rows.append(row)

    return pd.DataFrame(rows)


# --------------------------------------------------
# MAIN REPORT GENERATOR
# --------------------------------------------------
def generate_report(analysis_id, mode="Public", file_type="pdf"):
    db = get_db()

    students = fetch_analysis_data(db, analysis_id, mode)
    if not students:
        return None

    # 🔹 Build DataFrame
    df = build_dataframe(students)

    # 🔹 Use VALID analysis (not broken import)
    analysis_df = build_subject_analysis(df)

    # 🔹 Metadata
    department = students[0].get("department_name", "")
    semester = students[0].get("semester", "")
    batch = students[0].get("batch", "")

    report_id = str(uuid.uuid4())

    # 🔹 QR
    qr_path = generate_qr_code(report_id)

    os.makedirs("outputs/reports", exist_ok=True)

    # --------------------------------------------------
    # PDF
    # --------------------------------------------------
    if file_type == "pdf":
        file_path = f"outputs/reports/{report_id}.pdf"

        generate_pdf_report(
            df,
            analysis_df,
            file_path,
            report_id,
            qr_path,
            department,
            semester,
            batch,
            db=db,
            mode=mode
        )

    # --------------------------------------------------
    # EXCEL
    # --------------------------------------------------
    elif file_type == "excel":
        file_path = f"outputs/reports/{report_id}.xlsx"

        generate_excel_report(
            df,
            analysis_df,
            file_path,
            report_id,
            qr_path,
            department,
            semester,
            batch,
            db=db,
            mode=mode
        )

    # --------------------------------------------------
    # HTML
    # --------------------------------------------------
    elif file_type == "html":
        file_path = f"outputs/reports/{report_id}.html"

        html_content = generate_html_report(
            df,
            analysis_df,
            report_id,
            department,
            semester,
            batch,
            qr_path,
            db=db,
            mode=mode
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    else:
        raise ValueError("Invalid file type")

    # 🔹 Save metadata
    save_report_metadata(
        db,
        report_id,
        department,
        file_path,
        file_type
    )

    return file_path
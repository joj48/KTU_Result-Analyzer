import uuid
from app.core.core import process_result_file
from app.core.utils.db import save_structured_records_to_mongodb


# --------------------------------------------------
# UPLOAD HANDLER
# --------------------------------------------------

def handle_upload(file_path, department, db, mode):
    import uuid

    headers, students, semester, batch = process_result_file(
        file_path,
        department,
        db,
        mode
    )

    analysis_id = str(uuid.uuid4())

    save_structured_records_to_mongodb(
        students,
        department,
        semester=semester,
        upload_id=analysis_id,
        mode=mode
    )

    # 🔥 SUMMARY (UI CARDS)
    total_students = len(students)
    passed = len([s for s in students if s.get("SGPA", 0) > 0])
    failed = total_students - passed

    avg_sgpa = round(
        sum([s.get("SGPA", 0) for s in students]) / total_students, 2
    ) if total_students else 0

    summary = {
        "total_students": total_students,
        "avg_score": avg_sgpa,
        "pass_rate": round((passed / total_students) * 100, 2) if total_students else 0,
        "failed": failed
    }

    for student in students:
        student.pop("_id", None)

    return {
        "analysis_id": analysis_id,
        "summary": summary,
        "students": students,
        "headers": headers,
        "batch": batch,
        "semester": semester
    }


# --------------------------------------------------
# FETCH RESULTS FOR ALL STUDENTS 
# --------------------------------------------------

def get_results(db, user, batch=None, department=None):
    collection = db["Result_Private"] if user else db["Result_Public"]

    query = {}

    if batch:
        query["batch"] = batch

    if department:
        query["department_name"] = department

    return list(collection.find(query, {"_id": 0}))

# --------------------------------------------------
# FETCH RESULTS FOR A SINGLE STUDENT
# --------------------------------------------------
def get_result_by_reg_no(db, reg_no, user):
    collection = db["Result_Private"] if user else db["Result_Public"]

    return collection.find_one({"reg_no": reg_no}, {"_id": 0})
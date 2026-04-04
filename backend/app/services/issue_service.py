from datetime import datetime
from bson import ObjectId
from app.core.utils.db import get_db


async def create_issue(issue_data: dict):
    db = get_db()

    issue_data.update({
        "status": "open",   # default status
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    result = db["issues"].insert_one(issue_data)

    return str(result.inserted_id)
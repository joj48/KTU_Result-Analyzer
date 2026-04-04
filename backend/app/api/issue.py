from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from app.schemas.issue_schema import IssueCreate
from app.services.issue_service import create_issue
from app.dependencies.auth_deps import verify_token

router = APIRouter(prefix="/issues", tags=["Issues"])

@router.post("/")
async def report_issue(issue: IssueCreate, user=Depends(verify_token)):
    issue_id = await create_issue(issue.dict())
    
    return {
        "message": "Issue reported successfully",
        "issue_id": issue_id
    }
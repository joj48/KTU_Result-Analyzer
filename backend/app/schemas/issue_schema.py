from pydantic import BaseModel, EmailStr
from typing import List, Optional

class IssueCreate(BaseModel):
    title: str
    category: str
    severity: str
    description: str
    steps_to_reproduce: Optional[List[str]] = []
    email: EmailStr
    name: Optional[str] = None
    page_url: Optional[str] = None

class IssueResponse(IssueCreate):
    id: str
    status: str
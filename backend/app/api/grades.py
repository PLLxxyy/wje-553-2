from decimal import Decimal
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.enums import GradeStatus
from app.core.permissions import require_permission
from app.services.grade_service import grade_service

router = APIRouter(prefix="/grades", tags=["grades"])

class GradePayload(BaseModel):
    score: Decimal
    comment: str | None = None

class PublishPayload(BaseModel):
    assignment_id: str | None = None
    submission_ids: list[str] | None = None

def serialize_submission(item):
    return {
        "id": str(item.id),
        "assignment_id": str(item.assignment_id),
        "student_id": str(item.student_id),
        "student_name": item.student.name if item.student else None,
        "score": float(item.score) if item.score else None,
        "comment": item.comment,
        "grade_status": item.grade_status.value,
        "graded_at": item.graded_at.isoformat() if item.graded_at else None,
        "submitted_at": item.submitted_at.isoformat() if item.submitted_at else None,
    }

@router.get("/summary")
def grade_summary(course_id: str | None = None, db: Session = Depends(get_db), request: Request = None):
    role = request.state.user.get("role") if hasattr(request, "state") and hasattr(request.state, "user") else None
    return grade_service.course_summary(db, course_id, role=role)

@router.get("/submissions")
def list_graded(assignment_id: str | None = None, grade_status: GradeStatus | None = None, db: Session = Depends(get_db), request: Request = None):
    role = request.state.user.get("role") if hasattr(request, "state") and hasattr(request.state, "user") else None
    items = grade_service.list_graded(db, assignment_id=assignment_id, grade_status=grade_status, role=role)
    return [serialize_submission(s) for s in items]

@router.post("/{submission_id}/grade")
def grade_a_submission(submission_id: str, payload: GradePayload, request: Request, db: Session = Depends(get_db)):
    require_permission(request.state.user.get("role"), "grades:write")
    item = grade_service.grade_submission(db, submission_id, payload.score, payload.comment, request.state.user.get("id"))
    return serialize_submission(item)

@router.post("/publish")
def publish_grades(payload: PublishPayload, request: Request, db: Session = Depends(get_db)):
    require_permission(request.state.user.get("role"), "grades:publish")
    count = grade_service.publish_grades(db, assignment_id=payload.assignment_id, submission_ids=payload.submission_ids, user_id=request.state.user.get("id"))
    return {"published_count": count}

@router.get("/comprehensive/{course_id}/{student_id}")
def student_comprehensive(course_id: str, student_id: str, db: Session = Depends(get_db)):
    score = grade_service.student_comprehensive(db, course_id, student_id)
    return {"course_id": course_id, "student_id": student_id, "comprehensive_score": score}

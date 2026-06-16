from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.core.enums import GradeStatus
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.student import Student
from .audit_service import audit_service

class GradeService:
    def grade_submission(self, db: Session, submission_id: str, score: Decimal, comment: str | None = None, user_id: str | None = None) -> Submission:
        submission = db.query(Submission).options(joinedload(Submission.student), joinedload(Submission.assignment)).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        before = {"score": float(submission.score) if submission.score else None, "grade_status": submission.grade_status.value}
        submission.score = score
        submission.comment = comment
        submission.graded_at = datetime.now()
        submission.grade_status = GradeStatus.DRAFT
        db.commit(); db.refresh(submission)
        db.refresh(submission, ["student", "assignment"])
        audit_service.log(db, "grade.create", "Submission", str(submission.id), user_id=user_id, before_data=before, after_data={"score": float(score), "grade_status": GradeStatus.DRAFT.value})
        return submission

    def publish_grades(self, db: Session, assignment_id: str | None = None, submission_ids: list[str] | None = None, user_id: str | None = None) -> int:
        query = db.query(Submission).filter(Submission.score.isnot(None), Submission.grade_status == GradeStatus.DRAFT)
        if assignment_id:
            query = query.filter(Submission.assignment_id == assignment_id)
        if submission_ids:
            query = query.filter(Submission.id.in_(submission_ids))
        submissions = query.all()
        if not submissions:
            return 0
        for s in submissions:
            s.grade_status = GradeStatus.PUBLISHED
        db.commit()
        audit_service.log(db, "grade.publish", "Assignment", assignment_id or "batch", user_id=user_id, after_data={"count": len(submissions)})
        return len(submissions)

    def list_graded(self, db: Session, assignment_id: str | None = None, grade_status: GradeStatus | None = None, role: str | None = None):
        query = db.query(Submission).options(joinedload(Submission.student), joinedload(Submission.assignment)).filter(Submission.score.isnot(None))
        if assignment_id:
            query = query.filter(Submission.assignment_id == assignment_id)
        if grade_status:
            query = query.filter(Submission.grade_status == grade_status)
        if role == "STUDENT":
            query = query.filter(Submission.grade_status == GradeStatus.PUBLISHED)
        return query.order_by(Submission.graded_at.desc()).all()

    def course_summary(self, db: Session, course_id: str | None = None, role: str | None = None):
        query = db.query(Submission).join(Submission.assignment).filter(Submission.score.isnot(None))
        if course_id:
            query = query.filter(Assignment.course_id == course_id)
        if role == "STUDENT":
            query = query.filter(Submission.grade_status == GradeStatus.PUBLISHED)
        submissions = query.all()
        scores = [float(s.score) for s in submissions]
        if not scores:
            return {"average": 0, "highest": 0, "lowest": 0, "pass_rate": 0, "rows": []}
        return {
            "average": round(sum(scores) / len(scores), 1),
            "highest": max(scores),
            "lowest": min(scores),
            "pass_rate": round(len([s for s in scores if s >= 60]) / len(scores) * 100, 1),
            "rows": [],
        }

    def student_comprehensive(self, db: Session, course_id: str, student_id: str) -> float:
        submissions = (
            db.query(Submission).options(joinedload(Submission.assignment))
            .join(Submission.assignment)
            .filter(Assignment.course_id == course_id, Submission.student_id == student_id, Submission.grade_status == GradeStatus.PUBLISHED)
            .all()
        )
        if not submissions:
            return 0.0
        total_weight = sum(float(s.assignment.weight or 0) for s in submissions)
        if total_weight == 0:
            scores = [float(s.score or 0) for s in submissions]
            return round(sum(scores) / len(scores), 1)
        weighted_sum = sum(float(s.score or 0) * float(s.assignment.weight or 0) / float(s.assignment.total_score or 100) for s in submissions)
        return round(weighted_sum / total_weight * 100, 1)

grade_service = GradeService()

from app.models.academic import Course, Enrollment, Evaluation, EvaluationGrade, Student, Subject
from app.models.ai_config import AIModelConfig
from app.models.user import User

__all__ = [
	"User",
	"Subject",
	"Course",
	"Student",
	"Evaluation",
	"Enrollment",
	"EvaluationGrade",
	"AIModelConfig",
]

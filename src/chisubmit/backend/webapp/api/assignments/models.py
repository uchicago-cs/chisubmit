from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.json import Serializable
import math
from chisubmit.backend.webapp.api.types import UTCDateTime


class Assignment(Serializable):
    __tablename__ = 'assignments'
    id = db.Column(db.Unicode, primary_key=True)
    name = db.Column(db.Unicode)
    deadline = db.Column(UTCDateTime)
    course_id = db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    grade_components = db.relationship("GradeComponent", backref="assignment")
    default_fields = ['id', 'deadline', 'course_id', 'grade_components',
                      'name']
    readonly_fields = ['deadline', 'id', 'name', 'grade_components']

    def extensions_needed(self, submission_time):
        delta = (submission_time - self.deadline).total_seconds()

        extensions_needed = math.ceil(delta / (3600.0 * 24))

        if extensions_needed <= 0:
            return 0
        else:
            return int(extensions_needed)
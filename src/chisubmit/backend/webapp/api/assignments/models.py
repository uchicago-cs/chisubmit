from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.json import Serializable


class Assignment(Serializable):
    __tablename__ = 'assignments'
    id = db.Column(db.Unicode, primary_key=True)
    name = db.Column(db.Unicode)
    deadline = db.Column(db.DateTime)
    course_id = db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    grade_components = db.relationship("GradeComponent", backref="assignment")
    default_fields = ['id', 'deadline', 'course_id', 'grade_components',
                      'name']
    readonly_fields = ['deadline', 'id', 'name', 'grade_components']

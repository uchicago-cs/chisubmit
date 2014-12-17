from api import db
from api.models.json import Serializable


class Project(Serializable):
    __tablename__ = 'projects'
    id = db.Column(db.Unicode, primary_key=True)
    name = db.Column(db.Unicode)
    deadline = db.Column(db.DateTime)
    course_id = db.Column('course_id', db.Integer, db.ForeignKey('courses.id'))
    grade_components = db.relationship("GradeComponent", backref="project")
    default_fields = ['id', 'deadline', 'course_id', 'grade_components',
                      'name']
    readonly_fields = ['deadline', 'id', 'name', 'grade_components']

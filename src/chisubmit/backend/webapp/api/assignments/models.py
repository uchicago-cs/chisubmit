from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.json import Serializable
import math
from chisubmit.backend.webapp.api.types import UTCDateTime

class Assignment(Serializable):
    __tablename__ = 'assignments'
    id = db.Column(db.Unicode, primary_key=True)
    course_id = db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)

    name = db.Column(db.Unicode)
    deadline = db.Column(UTCDateTime)
    grade_components = db.relationship("GradeComponent", backref="assignment")
    
    default_fields = ['id', 'name', 'deadline', 'course_id', 
                      'grade_components']
    readonly_fields = ['id', 'grade_components', 'course_id']
    
    @staticmethod
    def from_id(course_id, assignment_id):
        return Assignment.query.filter_by(id=assignment_id, course_id=course_id).first()    
    
        
class GradeComponent(Serializable, db.Model):
    __tablename__ = 'grade_components'
    id = db.Column(db.Unicode, primary_key=True)
    course_id = db.Column('course_id', db.Integer, primary_key=True)
    assignment_id = db.Column('assignment_id', db.Integer, primary_key=True)

    order = db.Column(db.Integer)
    description = db.Column(db.Unicode)
    points = db.Column('points', db.Float)
    
    default_fields = ['id', 'description', 'order', 'points', 'assignment_id']
    readonly_fields = ['id', 'course_id', 'assignment_id']
    
    __table_args__ = (db.ForeignKeyConstraint([assignment_id, course_id],
                                              [Assignment.id, Assignment.course_id]),
                      {})

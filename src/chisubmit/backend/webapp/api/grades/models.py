from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.json import Serializable


class GradeComponent(Serializable, db.Model):
    __tablename__ = 'grade_components'
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)        
    name = db.Column(db.Unicode)
    points = db.Column('points', db.Integer)
    assignment_id = db.Column('assignment_id',
                           db.Integer,
                           db.ForeignKey('assignments.id'))
    grades = db.relationship('Grade', back_populates='grade_component')
    default_fields = ['name', 'points', 'assignment_id']
    readonly_fields = ['name', 'assignment_id']


class Grade(Serializable, db.Model):
    __tablename__ = 'grades'
    points = db.Column(db.Integer, nullable=False)
    course_id = db.Column('course_id', 
                          db.Integer, primary_key=True)
    assignment_id = db.Column('assignment_id', db.Integer,
                           db.ForeignKey('assignments.id'), primary_key=True)
    team_id = db.Column('team_id',
                        db.Integer,
                        db.ForeignKey('teams.id'), primary_key=True)
    grade_component_id = db.Column('grade_component_id',
                                     db.Unicode,
                                     db.ForeignKey('grade_components.id'),
                                     primary_key=True)
    grade_component = db.relationship('GradeComponent',
                                      back_populates='grades')
    default_fields = ['id', 'points', 'grade_component']
    readonly_fields = ['id', 'team', 'grade_component']
 

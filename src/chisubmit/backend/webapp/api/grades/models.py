from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.json import Serializable


class GradeComponent(Serializable, db.Model):
    __tablename__ = 'grade_components'
    name = db.Column(db.Unicode, primary_key=True)
    points = db.Column('points', db.Integer)
    assignment_id = db.Column('assignment_id',
                           db.Integer,
                           db.ForeignKey('assignments.id'), primary_key=True)
    grades = db.relationship('Grade', back_populates='grade_component')
    default_fields = ['name', 'points', 'assignment_id']
    readonly_fields = ['name', 'assignment_id']


class Grade(Serializable, db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer, nullable=False)
    assignment_team_id = db.Column('assignment_team_id', db.Integer,
                                db.ForeignKey('assignments_teams.id'))
    assignment_id = db.Column('assignment_id', db.Integer,
                           db.ForeignKey('assignments.id'))
    team_id = db.Column('team_id',
                        db.Integer,
                        db.ForeignKey('teams.id'))
    grade_component_name = db.Column('grade_component_name',
                                     db.Unicode,
                                     db.ForeignKey('grade_components.name'))
    grade_component = db.relationship('GradeComponent',
                                      back_populates='grades')
    assignments_teams = db.relationship('AssignmentsTeams', backref='grades')
    default_fields = ['id', 'points', 'grade_component']
    readonly_fields = ['id', 'team', 'grade_component']

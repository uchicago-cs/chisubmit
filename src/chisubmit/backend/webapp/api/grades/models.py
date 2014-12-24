from api import db
from api.models.json import Serializable


class GradeComponent(Serializable, db.Model):
    __tablename__ = 'grade_components'
    name = db.Column(db.Unicode, primary_key=True)
    points = db.Column('points', db.Integer)
    project_id = db.Column('project_id',
                           db.Integer,
                           db.ForeignKey('projects.id'), primary_key=True)
    grades = db.relationship('Grade', back_populates='grade_component')
    default_fields = ['name', 'points', 'project_id']
    readonly_fields = ['name', 'project_id']


class Grade(Serializable, db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer, nullable=False)
    project_team_id = db.Column('project_team_id', db.Integer,
                                db.ForeignKey('projects_teams.id'))
    project_id = db.Column('project_id', db.Integer,
                           db.ForeignKey('projects.id'))
    team_id = db.Column('team_id',
                        db.Integer,
                        db.ForeignKey('teams.id'))
    grade_component_name = db.Column('grade_component_name',
                                     db.Unicode,
                                     db.ForeignKey('grade_components.name'))
    grade_component = db.relationship('GradeComponent',
                                      back_populates='grades')
    projects_teams = db.relationship('ProjectsTeams', backref='grades')
    default_fields = ['id', 'points', 'grade_component']
    readonly_fields = ['id', 'team', 'grade_component']

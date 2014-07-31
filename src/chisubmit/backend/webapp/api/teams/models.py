from api import db
from sqlalchemy.ext.associationproxy import association_proxy
from api.graders.models import Grader


class StudentsTeams(db.Model):
    __tablename__ = 'students_teams'
    status = db.Column(db.Integer, nullable=False, server_default='0')
    student_id = db.Column('student_id',
                           db.Unicode,
                           db.ForeignKey('students.student_id'),
                           primary_key=True)
    team_id = db.Column('team_id',
                        db.Integer,
                        db.ForeignKey('teams.team_id'),
                        primary_key=True)
    student = db.relationship("Student")
    team = db.relationship("Team",
                           backref=db.backref("students_teams",
                                              cascade="all, delete-orphan"))


class ProjectsTeams(db.Model):
    # TODO 31JULY14: grades and penalties. There are no tables nor relationships for those things yet
    __tablename__ = 'projects_teams'
    extensions_used = db.Column(db.Integer)
    
    project_id = db.Column('project_id',
                           db.Integer,
                           db.ForeignKey('projects.project_id'),
                           primary_key=True)
    grader_id = db.Column('grader_id',
                           db.Integer,
                           db.ForeignKey('graders.grader_id'),
                           primary_key=True)
    team_id = db.Column('team_id',
                        db.Unicode,
                        db.ForeignKey('teams.team_id'),
                        primary_key=True)
    team = db.relationship("Team",
                           backref=db.backref("projects_teams",
                                              cascade="all, delete-orphan"))
    project = db.relationship("Project")
    grader = db.relationship("Grader")


class Team(db.Model):
    __tablename__ = 'teams'
    team_id = db.Column(db.Unicode, primary_key=True)
    private_name = db.Column(db.Unicode)
    git_repo_created = db.Column(db.Boolean,
                                 server_default='0', nullable=False)
    git_staging_repo_created = db.Column(db.Boolean,
                                         server_default='0', nullable=False)
    active = db.Column('active', db.Boolean,
                       server_default='1', nullable=False)
    course_id = db.Column('course_id',
                          db.Integer, db.ForeignKey('courses.course_id'))
    students = db.relationship('StudentsTeams', cascade="all, delete-orphan")
    projects = db.relationship('ProjectsTeams', cascade="all, delete-orphan")

from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.json import Serializable
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from chisubmit.backend.webapp.api.assignments.models import Assignment

class Team(Serializable, db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Unicode, primary_key=True)
    private_name = db.Column(db.Unicode)
    git_repo_created = db.Column(db.Boolean,
                                 server_default='0', nullable=False)
    git_staging_repo_created = db.Column(db.Boolean,
                                         server_default='0', nullable=False)
    active = db.Column('active', db.Boolean,
                       server_default='1', nullable=False)
    course_id = db.Column('course_id',
                          db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    students = association_proxy('students_teams', 'student')
    assignments = association_proxy('assignments_teams', 'assignment')
    grades = db.relationship('Grade', cascade="all, delete-orphan",
                             backref='team')
    default_fields = ['private_name', 'git_repo_created',
                      'git_staging_repo_created', 'active',
                      'students', 'assignments', 'assignments_teams', 'grades']
    readonly_fields = ['students', 'assignments', 'grades']


class StudentsTeams(Serializable, db.Model):
    STATUS_UNCONFIRMED = 0
    STATUS_CONFIRMED = 1
    
    __tablename__ = 'students_teams'
    status = db.Column(db.Integer, nullable=False, server_default='0')
    student_id = db.Column('student_id',
                           db.Unicode,
                           db.ForeignKey('users.id'),
                           primary_key=True)
    team_id = db.Column('team_id',
                        db.Integer,
                        primary_key=True)
    course_id = db.Column('course_id', 
                          db.Integer, 
                          primary_key=True)
    student = db.relationship("User")
    default_fields = ['status', 'student']
    readonly_fields = ['student', 'team']
    team = db.relationship("Team",
                           backref=db.backref("students_teams",
                                              cascade="all, delete-orphan"))
    __table_args__ = (db.ForeignKeyConstraint([team_id, course_id],
                                              [Team.id, Team.course_id]),
                      {})

class AssignmentsTeams(Serializable, db.Model):
    __tablename__ = 'assignments_teams'
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True)
    extensions_used = db.Column(db.Integer)

    UniqueConstraint('assignment_id', 'team_id')
    assignment_id = db.Column('assignment_id',
                           db.Integer)
    grader_id = db.Column('grader_id',
                          db.Integer,
                          db.ForeignKey('users.id'))
    team_id = db.Column('team_id',
                        db.Unicode)
    course_id = db.Column('course_id', 
                          db.Integer)
    team = db.relationship("Team",
                           backref=db.backref("assignments_teams",
                                              cascade="all, delete-orphan"))
    assignment = db.relationship("Assignment")
    grader = db.relationship("User")
    default_fields = ['id', 'extensions_used', 'assignment_id',
                      'grader_id', 'team_id', 'grades']
    readonly_fields = ['team', 'grader', 'grades']
    __table_args__ = (db.ForeignKeyConstraint([team_id, course_id],
                                              [Team.id, Team.course_id]),
                      db.ForeignKeyConstraint([assignment_id, course_id],
                                              [Assignment.id, Assignment.course_id]),
                      {})
    



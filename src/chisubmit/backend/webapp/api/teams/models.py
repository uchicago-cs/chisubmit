from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.json import Serializable
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy


class StudentsTeams(Serializable, db.Model):
    __tablename__ = 'students_teams'
    status = db.Column(db.Integer, nullable=False, server_default='0')
    student_id = db.Column('student_id',
                           db.Unicode,
                           db.ForeignKey('people.id'),
                           primary_key=True)
    team_id = db.Column('team_id',
                        db.Integer,
                        db.ForeignKey('teams.id'),
                        primary_key=True)
    student = db.relationship("Person")
    default_fields = ['status', 'student']
    readonly_fields = ['student', 'team']
    team = db.relationship("Team",
                           backref=db.backref("students_teams",
                                              cascade="all, delete-orphan"))


class ProjectsTeams(Serializable, db.Model):
    __tablename__ = 'projects_teams'
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True)
    extensions_used = db.Column(db.Integer)

    UniqueConstraint('project_id', 'team_id')
    project_id = db.Column('project_id',
                           db.Integer,
                           db.ForeignKey('projects.id'))
    grader_id = db.Column('grader_id',
                          db.Integer,
                          db.ForeignKey('people.id'))
    team_id = db.Column('team_id',
                        db.Unicode,
                        db.ForeignKey('teams.id'))
    team = db.relationship("Team",
                           backref=db.backref("projects_teams",
                                              cascade="all, delete-orphan"))
    project = db.relationship("Project")
    grader = db.relationship("Person")
    default_fields = ['id', 'extensions_used', 'project_id',
                      'grader_id', 'team_id', 'grades']
    readonly_fields = ['team', 'grader', 'grades']


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
                          db.Integer, db.ForeignKey('courses.id'))
    students = association_proxy('students_teams', 'student')
    projects = association_proxy('projects_teams', 'project')
    grades = db.relationship('Grade', cascade="all, delete-orphan",
                             backref='team')
    default_fields = ['private_name', 'git_repo_created',
                      'git_staging_repo_created', 'active',
                      'students', 'projects', 'projects_teams', 'grades']
    readonly_fields = ['students', 'projects', 'grades']

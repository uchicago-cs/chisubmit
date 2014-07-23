from api import db
from sqlalchemy.ext.associationproxy import association_proxy


class StudentsTeams(db.Model):
    __tablename__ = 'students_teams'
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
    __tablename__ = 'projects_teams'
    project_id = db.Column('project_id',
                           db.Integer,
                           db.ForeignKey('projects.project_id'),
                           primary_key=True)
    team_id = db.Column('team_id',
                        db.Unicode,
                        db.ForeignKey('teams.team_id'),
                        primary_key=True)
    team = db.relationship("Team",
                           backref=db.backref("projects_teams",
                                              cascade="all, delete-orphan"))
    project = db.relationship("Project")


class Team(db.Model):
    __tablename__ = 'teams'
    team_id = db.Column(db.Unicode, primary_key=True)
    private_name = db.Column(db.Unicode)
    github_repo = db.Column(db.Unicode)
    github_team = db.Column(db.Unicode)
    active = db.Column('active', db.Boolean,
                       server_default='1', nullable=False)
    github_email_sent = db.Column('github_email_sent',
                                  db.Boolean,
                                  server_default='0',
                                  nullable=False)
    course_id = db.Column('course_id',
                          db.Integer, db.ForeignKey('courses.course_id'))
    students = db.relationship('StudentsTeams', cascade="all, delete-orphan")
    projects = db.relationship('ProjectsTeams', cascade="all, delete-orphan")

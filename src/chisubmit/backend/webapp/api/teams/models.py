from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.json import Serializable
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from chisubmit.backend.webapp.api.assignments.models import Assignment
from chisubmit.backend.webapp.api.types import JSONEncodedDict, UTCDateTime

class Team(Serializable, db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Unicode, primary_key=True)
    extensions = db.Column(db.Integer)    
    repo_info = db.Column(JSONEncodedDict, default={})
    extras = db.Column(JSONEncodedDict, default={})
    active = db.Column('active', db.Boolean,
                       server_default='1', nullable=False)
    course_id = db.Column('course_id',
                          db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    students = association_proxy('students_teams', 'student')
    assignments = association_proxy('assignments_teams', 'assignment')
    grades = db.relationship('Grade', cascade="all, delete-orphan",
                             backref='team')
    default_fields = ['extensions', 'repo_info', 'active', 'course_id',
                      'students', 'assignments', 'assignments_teams', 'grades']
    readonly_fields = ['students', 'assignments', 'grades']
    
    @staticmethod
    def find_teams_with_students(course_id, students):
        q = Team.query.filter(Team.course_id == course_id,
                Team.students.any(
                    StudentsTeams.student_id.in_(
                        [s.id for s in students])))
        
        return q.all()       
    
    def get_extensions_used(self):
        extensions = 0
        for at in self.assignments_teams:
            extensions += at.extensions_used
        return extensions 
        
    def get_extensions_available(self):
        return self.extensions - self.get_extensions_used()

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

    extensions_used = db.Column(db.Integer, default = 0)
    commit_sha = db.Column(db.Unicode)
    submitted_at = db.Column(UTCDateTime)

    assignment_id = db.Column('assignment_id',
                           db.Integer, primary_key=True)
    grader_id = db.Column('grader_id',
                          db.Integer,
                          db.ForeignKey('users.id'))
    team_id = db.Column('team_id',
                        db.Unicode, primary_key=True)
    course_id = db.Column('course_id', 
                          db.Integer, primary_key=True)
    team = db.relationship("Team",
                           backref=db.backref("assignments_teams",
                                              cascade="all, delete-orphan"))
    assignment = db.relationship("Assignment")
    grader = db.relationship("User")
    default_fields = ['extensions_used', 'assignment_id',
                      'grader_id', 'team_id', 'grades']
    readonly_fields = ['team', 'grader', 'grades']
    __table_args__ = (db.ForeignKeyConstraint([team_id, course_id],
                                              [Team.id, Team.course_id]),
                      db.ForeignKeyConstraint([assignment_id, course_id],
                                              [Assignment.id, Assignment.course_id]),
                      {})
    

    @staticmethod
    def from_id(course_id, team_id, assignment_id):
        return AssignmentsTeams.query.filter_by(course_id=course_id,
                                                team_id=team_id,
                                                assignment_id=assignment_id).first()
                                    

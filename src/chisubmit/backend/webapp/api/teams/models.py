from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.json import Serializable
from chisubmit.backend.webapp.api.types import JSONEncodedDict, UTCDateTime
from chisubmit.backend.webapp.api.assignments.models import GradeComponent
from sqlalchemy.ext.associationproxy import association_proxy
from datetime import timedelta
from chisubmit.common.utils import get_datetime_now_utc

class Team(Serializable, db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Unicode, primary_key=True)
    extensions = db.Column(db.Integer, default=0)    
    repo_info = db.Column(JSONEncodedDict, default={})
    extras = db.Column(JSONEncodedDict, default={})
    active = db.Column('active', db.Boolean,
                       server_default='1', nullable=False)
    course_id = db.Column('course_id',
                          db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    students = association_proxy('students_teams', 'student')
    assignments = association_proxy('assignments_teams', 'assignment')

    default_fields = ['extensions', 'repo_info', 'active', 'course_id', 'extras',
                      'students_teams', 'assignments_teams', 'grades']
    readonly_fields = ['students', 'assignments', 'grades', 'extras']
    
    @staticmethod
    def from_id(course_id, team_id):
        return Team.query.filter_by(course_id=course_id,id=team_id).first()        
    
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
        
    def get_extensions_available(self, extension_policy):
        from chisubmit.backend.webapp.api.courses.models import CoursesStudents

        if extension_policy == "per_team":
            return self.extensions - self.get_extensions_used()    
        elif extension_policy == "per_student":
            student_extensions_available = []
            for student in self.students:
                cs = CoursesStudents.from_id(self.course_id, student.id)
                a = cs.get_extensions_available()
                student_extensions_available.append(a)
            return min(student_extensions_available)
        else:
            return 0        

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

    assignment_id = db.Column('assignment_id',
                           db.Integer, primary_key=True)
    team_id = db.Column('team_id',
                        db.Unicode, primary_key=True)
    course_id = db.Column('course_id', 
                          db.Integer, primary_key=True)

    extensions_used = db.Column(db.Integer, default = 0)
    commit_sha = db.Column(db.Unicode)
    submitted_at = db.Column(UTCDateTime)
    grader_id = db.Column('grader_id',
                          db.Integer,
                          db.ForeignKey('users.id'))
    penalties = db.Column(JSONEncodedDict, default={})


    team = db.relationship("Team",
                           backref=db.backref("assignments_teams",
                                              cascade="all, delete-orphan"))
    assignment = db.relationship("Assignment")
    grader = db.relationship("User")
    
    default_fields = ['extensions_used', 'commit_sha', 'submitted_at', 'assignment_id', 
                      'grades', 'penalties', 'grader']
    readonly_fields = ['team', 'grader', 'grades']
    __table_args__ = (db.ForeignKeyConstraint([team_id, course_id],
                                              [Team.id, Team.course_id]),
                      db.ForeignKeyConstraint([assignment_id, course_id],
                                              ["assignments.id", "assignments.course_id"]),
                      {})
    

    @staticmethod
    def from_id(course_id, team_id, assignment_id):
        return AssignmentsTeams.query.filter_by(course_id=course_id,
                                                team_id=team_id,
                                                assignment_id=assignment_id).first()
                                                
    def get_grade(self, gc_id):
        grades = [g for g in self.grades if g.grade_component_id == gc_id]
        if len(grades) == 0:
            return None
        else:
            return grades[0]           
        
    def is_ready_for_grading(self):
        if self.submitted_at is None:
            return False
        else:
            now = get_datetime_now_utc()
            deadline = self.assignment.deadline + timedelta(days=self.extensions_used)
            
            if now > deadline:
                return True
            else:
                return False
                                   
                                    
class Grade(Serializable, db.Model):
    __tablename__ = 'grades'

    course_id = db.Column('course_id', db.Integer, primary_key=True)
    assignment_id = db.Column('assignment_id', db.Integer, primary_key=True)
    grade_component_id = db.Column('grade_component_id',
                                     db.Unicode, primary_key=True)
    team_id = db.Column('team_id', db.Integer, primary_key=True)

    points = db.Column(db.Float, nullable=False)
    
    grade_component = db.relationship('GradeComponent')
    team = db.relationship('AssignmentsTeams', backref="grades")
    
    default_fields = ['points', 'grade_component_id']
    readonly_fields = ['course_id', 'team_id', 'grade_component']
 
    __table_args__ = (db.ForeignKeyConstraint([team_id, assignment_id, course_id],
                                              [AssignmentsTeams.team_id, AssignmentsTeams.assignment_id, AssignmentsTeams.course_id]),
                      db.ForeignKeyConstraint([grade_component_id, assignment_id, course_id],
                                              [GradeComponent.id, GradeComponent.assignment_id, GradeComponent.course_id]),
                      {})
        
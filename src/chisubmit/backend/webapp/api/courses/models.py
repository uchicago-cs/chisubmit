from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.mixins import ExposedModel
from chisubmit.backend.webapp.api.models.json import Serializable
from sqlalchemy.ext.associationproxy import association_proxy
from chisubmit.backend.webapp.api.types import JSONEncodedDict


class CoursesGraders(Serializable, db.Model):
    __tablename__ = 'courses_graders'
    repo_info = db.Column(JSONEncodedDict, default={})
    grader_id = db.Column('grader_id',
                          db.Unicode,
                          db.ForeignKey('users.id'), primary_key=True)
    course_id = db.Column('course_id',
                          db.Integer,
                          db.ForeignKey('courses.id'), primary_key=True)
    grader = db.relationship("User")
    
    # Dirty hack
    conflicts = db.Column(db.Unicode)
    
    default_fields = ['grader', 'repo_info', 'conflicts']
    readonly_fields = ['grader_id', 'course_id', 'repo_info']        
    course = db.relationship("Course",
                             backref=db.backref("courses_graders",
                                                cascade="all, delete-orphan"))


class CoursesStudents(Serializable, db.Model):
    __tablename__ = 'courses_students'
    repo_info = db.Column(JSONEncodedDict, default={})
    dropped = db.Column('dropped', db.Boolean, server_default='0',
                        nullable=False)
    extensions = db.Column(db.Integer, default=0)    

    student_id = db.Column('student_id',
                           db.Unicode,
                           db.ForeignKey('users.id'),
                           primary_key=True)
    course_id = db.Column('course_id',
                          db.Integer,
                          db.ForeignKey('courses.id'),
                          primary_key=True)
    student = db.relationship("User")
    default_fields = ['student', 'dropped', 'repo_info']
    readonly_fields = ['student_id', 'course_id', 'repo_info']    
    course = db.relationship("Course",
                             backref=db.backref("courses_students",
                                                cascade="all, delete-orphan"))

    @staticmethod
    def from_id(course_id, student_id):
        return CoursesStudents.query.filter_by(student_id=student_id, course_id=course_id).first()

    def get_extensions_available(self):
        from chisubmit.backend.webapp.api.teams.models import Team

        extensions_used = 0
        
        student_teams = Team.find_teams_with_students(self.course_id, [self.student])
        for student_team in student_teams:
            for assignment_team in student_team.assignments_teams:
                extensions_used += assignment_team.extensions_used

        return self.extensions - extensions_used
                

class CoursesInstructors(Serializable, db.Model):
    __tablename__ = 'courses_instructors'
    repo_info = db.Column(JSONEncodedDict, default={})
    instructor_id = db.Column('instructor_id',
                              db.Unicode,
                              db.ForeignKey('users.id'),
                              primary_key=True)
    course_id = db.Column('course_id',
                          db.Integer,
                          db.ForeignKey('courses.id'),
                          primary_key=True)
    instructor = db.relationship("User")
    default_fields = ['instructor', 'repo_info']
    readonly_fields = ['instructor_id', 'course_id', 'repo_info']    
    course = db.relationship("Course",
                             backref=db.backref("courses_instructors",
                                                cascade="all, delete-orphan"))


class Course(ExposedModel, Serializable):
    __tablename__ = 'courses'
    id = db.Column(db.Unicode, primary_key=True, unique=True)
    name = db.Column(db.Unicode)
    options = db.Column(JSONEncodedDict, default={})
    graders = association_proxy('courses_graders', 'grader')
    students = association_proxy('courses_students', 'student')
    instructors = association_proxy('courses_instructors', 'instructor')
    assignments = db.relationship("Assignment", backref="course")
    teams = db.relationship("Team", backref="course")
    default_fields = ['name', 'assignments', 'options']
    readonly_fields = ['id', 'options', 'graders', 'students', 'instructors',
                       'assignments', 'teams']
    
    @staticmethod
    def from_id(course_id):
        return Course.query.filter_by(id=course_id).first()
        

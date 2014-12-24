from api import db
from api.models.mixins import ExposedModel
from api.models.json import Serializable
from sqlalchemy.ext.associationproxy import association_proxy


class CoursesGraders(Serializable, db.Model):
    __tablename__ = 'courses_graders'
    git_server_id = db.Column(db.Unicode)
    git_staging_server_id = db.Column(db.Unicode)
    grader_id = db.Column('grader_id',
                          db.Unicode,
                          db.ForeignKey('people.id'), primary_key=True)
    course_id = db.Column('course_id',
                          db.Integer,
                          db.ForeignKey('courses.id'), primary_key=True)
    grader = db.relationship("Person")
    default_fields = ['course_id', 'grader_id']
    course = db.relationship("Course",
                             backref=db.backref("courses_graders",
                                                cascade="all, delete-orphan"))


class CoursesStudents(Serializable, db.Model):
    __tablename__ = 'courses_students'
    git_server_id = db.Column(db.Unicode)
    dropped = db.Column('dropped', db.Boolean, server_default='0',
                        nullable=False)
    student_id = db.Column('student_id',
                           db.Unicode,
                           db.ForeignKey('people.id'),
                           primary_key=True)
    course_id = db.Column('course_id',
                          db.Integer,
                          db.ForeignKey('courses.id'),
                          primary_key=True)
    student = db.relationship("Person")
    default_fields = ['course_id', 'student_id']
    course = db.relationship("Course",
                             backref=db.backref("courses_students",
                                                cascade="all, delete-orphan"))


class CoursesInstructors(Serializable, db.Model):
    __tablename__ = 'courses_instructors'
    git_server_id = db.Column(db.Unicode)
    git_staging_server_id = db.Column(db.Unicode)
    instructor_id = db.Column('instructor_id',
                              db.Unicode,
                              db.ForeignKey('people.id'),
                              primary_key=True)
    course_id = db.Column('course_id',
                          db.Integer,
                          db.ForeignKey('courses.id'),
                          primary_key=True)
    instructor = db.relationship("Person")
    default_fields = ['instructor']
    course = db.relationship("Course",
                             backref=db.backref("courses_instructors",
                                                cascade="all, delete-orphan"))


class Course(ExposedModel, Serializable):
    __tablename__ = 'courses'
    id = db.Column(db.Unicode, primary_key=True, unique=True)
    name = db.Column(db.Unicode)
    extensions = db.Column(db.Integer)
    git_server_connection_string = db.Column(db.Unicode)
    git_staging_server_connection_string = db.Column(db.Unicode)
    graders = association_proxy('courses_graders', 'grader')
    students = association_proxy('courses_students', 'student')
    instructors = association_proxy('courses_instructors', 'instructor')
    projects = db.relationship("Project", backref="course")
    teams = db.relationship("Team", backref="course")
    default_fields = ['name', 'extensions', 'students', 'instructors',
                      'projects', 'teams', 'graders',
                      'git_server_connection_string',
                      'git_staging_server_connection_string']
    readonly_fields = ['id', 'projects', 'instructors', 'students',
                       'graders', 'teams']

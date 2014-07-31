from api import db
from api.graders.models import Grader
from api.students.models import Student
from api.instructors.models import Instructor
from api.projects.models import Project
from api.teams.models import Team
from api.models.mixins import ExposedModel


class CoursesGraders(db.Model):
    __tablename__ = 'courses_graders'
    git_server_id = db.Column(db.Unicode)
    git_staging_server_id = db.Column(db.Unicode)
    grader_id = db.Column('grader_id',
                          db.Unicode,
                          db.ForeignKey('graders.grader_id'), primary_key=True)
    course_id = db.Column('course_id',
                          db.Integer,
                          db.ForeignKey('courses.course_id'), primary_key=True)
    grader = db.relationship("Grader")
    course = db.relationship("Course",
                             backref=db.backref("courses_graders",
                                                cascade="all, delete-orphan"))


class CoursesStudents(db.Model):
    __tablename__ = 'courses_students'
    git_server_id = db.Column(db.Unicode)
    dropped = db.Column('dropped', db.Boolean, server_default='0',
                        nullable=False)
    student_id = db.Column('student_id',
                           db.Unicode,
                           db.ForeignKey('students.student_id'),
                           primary_key=True)
    course_id = db.Column('course_id',
                          db.Integer,
                          db.ForeignKey('courses.course_id'),
                          primary_key=True)
    student = db.relationship("Student")
    course = db.relationship("Course",
                             backref=db.backref("courses_students",
                                                cascade="all, delete-orphan"))

class CoursesInstructors(db.Model):
    __tablename__ = 'courses_instructors'
    git_server_id = db.Column(db.Unicode)
    git_staging_server_id = db.Column(db.Unicode)
    instructor_id = db.Column('instructor_id',
                           db.Unicode,
                           db.ForeignKey('instructors.instructor_id'),
                           primary_key=True)
    course_id = db.Column('course_id',
                          db.Integer,
                          db.ForeignKey('courses.course_id'),
                          primary_key=True)
    instructor = db.relationship("Instructor")
    course = db.relationship("Course",
                             backref=db.backref("courses_instructors",
                                                cascade="all, delete-orphan"))


class Course(ExposedModel, db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Unicode, primary_key=True, unique=True)
    name = db.Column(db.Unicode)
    extensions = db.Column(db.Integer)
    git_server_connection_string = db.Column(db.Unicode)
    git_staging_server_connection_string = db.Column(db.Unicode)
    students = db.relationship('CoursesStudents',
                               cascade="all, delete-orphan")
    graders = db.relationship('CoursesGraders',
                              cascade="all, delete-orphan")
    instructors = db.relationship('CoursesInstructors',
                              cascade="all, delete-orphan")
    projects = db.relationship("Project", backref="course")
    teams = db.relationship("Team", backref="course")

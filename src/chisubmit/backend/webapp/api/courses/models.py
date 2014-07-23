from api import db
from api.graders.models import Grader
from api.students.models import Student
from api.projects.models import Project
from api.teams.models import Team
from api.models.mixins import ExposedModel


class CoursesGraders(db.Model):
    __tablename__ = 'courses_graders'
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
    student_id = db.Column('student_id',
                           db.Unicode,
                           db.ForeignKey('students.student_id'),
                           primary_key=True)
    course_id = db.Column('course_id',
                          db.Integer,
                          db.ForeignKey('courses.course_id'),
                          primary_key=True)
    dropped = db.Column('dropped', db.Boolean, server_default='0',
                        nullable=False)
    student = db.relationship("Student")
    course = db.relationship("Course",
                             backref=db.backref("courses_students",
                                                cascade="all, delete-orphan"))


class Course(ExposedModel, db.Model):
    attr_accessible = ('github_organization', 'name',
                       'extensions', 'github_admins_team',
                       'git_staging_username', 'git_staging_hostname')

    __tablename__ = 'courses'
    id = db.Column(db.Integer, autoincrement=True, unique=True)
    course_id = db.Column(db.Unicode, primary_key=True, unique=True)
    name = db.Column(db.Unicode)
    github_organization = db.Column(db.Unicode)
    github_admins_team = db.Column(db.Unicode)
    git_staging_username = db.Column(db.Unicode)
    git_staging_hostname = db.Column(db.Unicode)
    extensions = db.Column(db.Integer)

    # students = association_proxy('courses_students',
    #            'student',
    #            creator=lambda student: CoursesStudents(student=student))
    students = db.relationship('CoursesStudents',
                               cascade="all, delete-orphan")
    graders = db.relationship('CoursesGraders',
                              cascade="all, delete-orphan")
    # graders = association_proxy('courses_graders',
    #               'grader',
    #                creator=lambda grader: CoursesGraders(grader=grader))
    projects = db.relationship("Project", backref="course")
    teams = db.relationship("Team", backref="course")

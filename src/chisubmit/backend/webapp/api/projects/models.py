from api import db
from sqlalchemy.ext.associationproxy import association_proxy


class Project(db.Model):
    __tablename__ = 'projects'
    project_id = db.Column(db.Unicode, primary_key=True)
    name = db.Column(db.Unicode)
    deadline = db.Column(db.DateTime)
    course_id = db.Column('course_id', db.Integer, db.ForeignKey('courses.id'))
    grade_components = db.relationship("GradeComponent", backref="project")


class GradeComponent(db.Model):
    __tablename__ = 'grade_components'
    name = db.Column('name', db.Unicode, primary_key=True)
    project_id = db.Column('project_id',
                           db.Integer,
                           db.ForeignKey('projects.project_id'),
                           primary_key=True)
    points = db.Column('points', db.Integer)

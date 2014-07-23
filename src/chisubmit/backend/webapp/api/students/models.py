from api import db
from sqlalchemy.ext.associationproxy import association_proxy
from api.models.mixins import UniqueModel


class Student(UniqueModel, db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Unicode, primary_key=True)
    first_name = db.Column(db.Unicode)
    last_name = db.Column(db.Unicode)
    email = db.Column(db.Unicode)
    github_id = db.Column(db.Unicode)

    @classmethod
    def unique_hash(cls, **kws):
        return kws['student_id']

    @classmethod
    def unique_filter(cls, query, **kws):
        return query.filter(Student.student_id == kws['student_id'])

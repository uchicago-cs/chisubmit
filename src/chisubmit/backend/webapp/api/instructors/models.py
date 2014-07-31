from api import db
from sqlalchemy.ext.associationproxy import association_proxy
from api.models.mixins import UniqueModel


class Instructor(UniqueModel, db.Model):
    __tablename__ = 'instructors'
    instructor_id = db.Column(db.Unicode, primary_key=True)
    first_name = db.Column(db.Unicode)
    last_name = db.Column(db.Unicode)
    email = db.Column(db.Unicode)

    @classmethod
    def unique_hash(cls, **kws):
        return kws['student_id']

    @classmethod
    def unique_filter(cls, query, **kws):
        return query.filter(Instructor.instructor_id == kws['instructor_id'])

from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.models.mixins import UniqueModel
from chisubmit.backend.webapp.api.models.json import Serializable


class User(UniqueModel, Serializable, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Unicode, primary_key=True)
    first_name = db.Column(db.Unicode)
    last_name = db.Column(db.Unicode)
    email = db.Column(db.Unicode)
    api_key = db.Column(db.Unicode)
    admin = db.Column('admin', db.Boolean, server_default='0', nullable=False)
    default_fields = ['id', 'first_name', 'last_name', 'email']
    readonly_fields = ['id']

    @classmethod
    def unique_hash(cls, **kws):
        return kws['id']

    @classmethod
    def unique_filter(cls, query, **kws):
        return query.filter(User.id == kws['id'])
    
    @staticmethod
    def from_id(user_id):
        return User.query.filter_by(id=user_id).first()    
    
    def is_instructor_in(self, course):
        return self in course.instructors        

    def is_student_in(self, course):
        return self in course.students        

    def is_grader_in(self, course):
        return self in course.graders        

    def has_instructor_or_grader_permissions(self, course):
        return self.is_instructor_in(course) or self.is_grader_in(course) or self.admin

    def is_in_course(self, course):
        return self.is_instructor_in(course) or self.is_student_in(course) or self.is_grader_in(course)
    

from api import db
from api.models.mixins import UniqueModel


class Grader(UniqueModel, db.Model):
    __tablename__ = 'graders'
    grader_id = db.Column(db.Unicode, primary_key=True, unique=True)
    first_name = db.Column(db.Unicode)
    last_name = db.Column(db.Unicode)
    email = db.Column(db.Unicode)

    @classmethod
    def unique_hash(cls, **kws):
        return kws['grader_id']

    @classmethod
    def unique_filter(cls, query, **kws):
        return query.filter(Grader.id == kws['grader_id'])

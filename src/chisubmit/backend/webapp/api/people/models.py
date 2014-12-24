from api import db
from api.models.mixins import UniqueModel
from api.models.json import Serializable


class Person(UniqueModel, Serializable, db.Model):
    __tablename__ = 'people'
    id = db.Column(db.Unicode, primary_key=True)
    first_name = db.Column(db.Unicode)
    last_name = db.Column(db.Unicode)
    email = db.Column(db.Unicode)
    api_key = db.Column(db.Unicode)
    admin = db.Column('admin', db.Boolean, server_default='0', nullable=False)
    git_server_id = db.Column(db.Unicode)
    default_fields = ['id', 'first_name', 'last_name',
                      'email', 'git_server_id', 'git_staging_server_id']
    readonly_fields = ['id']

    @classmethod
    def unique_hash(cls, **kws):
        return kws['id']

    @classmethod
    def unique_filter(cls, query, **kws):
        return query.filter(Person.id == kws['id'])

import os
_basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'api.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(_basedir, 'db_repository')
DATABASE_CONNECT_OPTIONS = {}

THREADS_PER_PAGE = 8
DEBUG = True

# FIXME 23JULY14: doesn't seem to work?
TESTING = True
SQLALCHEMY_RECORD_QUERIES = True

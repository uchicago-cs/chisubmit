#!/usr/bin/env python

from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from api import db

db.create_all()

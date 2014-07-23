#!/usr/bin/env python

from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from api import db
import os.path

db.create_all()

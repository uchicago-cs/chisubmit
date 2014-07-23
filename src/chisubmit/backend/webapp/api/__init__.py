from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restless import APIManager, ProcessingException

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)


def auth_required(*args, **kw):
    auth = request.authorization
    if not auth or not cancan(auth.username, auth.password):
        pass
        # TODO 22JULY14: authentication token and permissions model
        # app.logger.info("This user is not authorized")
        # raise ProcessingException(description='Not authenticated!', code=401)
        # raise ProcessingException(description='Not authorized!', code=401)

manager = APIManager(app, preprocessors=dict(GET_SINGLE=[auth_required],
                     GET_MANY=[auth_required], PATCH_SINGLE=[auth_required],
                     PATCH_MANY=[auth_required], POST=[auth_required],
                     DELETE=[auth_required]), flask_sqlalchemy_db=db)

import api.views

from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from auth import ldapclient
from api.blueprints import api_endpoint
from api.json_encoder import CustomJSONEncoder

import wtforms_json
wtforms_json.init()

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

app.config.from_object('config')
db = SQLAlchemy(app)


def auth_required(*args, **kw):
    auth = request.authorization
    if not auth or not ldapclient.authenticate(auth.username, auth.password):
        pass
        # TODO 22JULY14: authentication token and permissions model
        # app.logger.info("This user is not authorized")
        # raise ProcessingException(description='Not authenticated!', code=401)
        # raise ProcessingException(description='Not authorized!', code=401)

from api.models.json import JSONEncoder
import api.views
app.register_blueprint(api_endpoint, url_prefix='/api/v0')

from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from api.blueprints import api_endpoint
from api.json_encoder import CustomJSONEncoder

import wtforms_json
wtforms_json.init()

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

app.config.from_object('config')
db = SQLAlchemy(app)

from api.models.json import JSONEncoder
import api.views
app.register_blueprint(api_endpoint, url_prefix='/api/v0')

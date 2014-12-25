from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from chisubmit.backend.webapp.api.json_encoder import CustomJSONEncoder

import wtforms_json
wtforms_json.init()

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

app.config.from_object('chisubmit.backend.webapp.config')
db = SQLAlchemy(app)

from chisubmit.backend.webapp.api.models.json import JSONEncoder
import chisubmit.backend.webapp.api.views
app.register_blueprint(api_endpoint, url_prefix='/api/v0')

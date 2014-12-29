import os.path

from chisubmit.common import ChisubmitException
from chisubmit.common.utils import gen_api_key
from chisubmit.backend.webapp.api.json_encoder import CustomJSONEncoder
from chisubmit.backend.webapp.api.blueprints import api_endpoint

from flask.app import Flask
from flask.ext.sqlalchemy import SQLAlchemy

import wtforms_json

wtforms_json.init()

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

db = SQLAlchemy(app)

from chisubmit.backend.webapp.api.models.json import JSONEncoder
import chisubmit.backend.webapp.api.views
app.register_blueprint(api_endpoint, url_prefix='/api/v0')


class ChisubmitAPIServer(object):

    def __init__(self, debug):
        self.app = app        
        self.db = db
        self.debug = debug
                    
        if self.debug:
            self.debug = True
            self.app.config["DEBUG"] = True
            self.app.config["TESTING"] = True
            self.app.config["SQLALCHEMY_RECORD_QUERIES"] = True
        else:
            self.debug = False
            
            
    def connect_sqlite(self, dbfile):
        self.app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + dbfile
        
    def connect_postgres(self):
        pass

    def start(self):
        self.app.run(debug = self.debug)
        
    def init_db(self, drop_all=False):
        if drop_all:
            self.db.drop_all()
        self.db.create_all()

    def create_admin(self, api_key=None):
        from chisubmit.backend.webapp.api.users.models import User

        admin = User.query.filter_by(id=u"admin").first()
        
        if admin is not None:
            return None
        
        if api_key is None:
            api_key = gen_api_key()
            
        admin = User(first_name=u"Administrator", 
                       last_name=u"Administrator", 
                       id=u"admin",
                       api_key=unicode(api_key), 
                       admin=1)
        
        self.db.session.add(admin)
        self.db.session.commit()
        
        return api_key
            
        
        


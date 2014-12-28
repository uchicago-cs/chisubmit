from chisubmit.backend.webapp.api import app, db
from chisubmit.backend.webapp.manage import manager
from chisubmit.backend.webapp.api.users.models import User
from chisubmit.common import ChisubmitException
from chisubmit.common.utils import gen_api_key

class ChisubmitServer(object):

    def __init__(self):
        self.app = app        
        self.db = db
        self.manager = manager

    def start(self):
        self.app.run(debug=True)
        
    def init_db(self):
        self.db.create_all()

    def create_admin(self, api_key=None):
        admin = User.query.filter_by(id="admin").first()
        
        if admin is not None:
            return None
        
        if api_key is None:
            api_key = gen_api_key()
            
        admin = User(first_name="Administrator", 
                       last_name="Administrator", 
                       id="admin",
                       api_key=api_key, 
                       admin=1)
        
        db.session.add(admin)
        db.session.commit()
        
        return api_key
            
        
        
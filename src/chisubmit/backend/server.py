from chisubmit.backend.webapp.api import app, db

class ChisubmitServer(object):

    def __init__(self):
        self.app = app        
        self.db = db

    def start(self):
        self.app.run(debug=True)
        
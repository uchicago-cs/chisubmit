import abc
from functools import wraps
from flask import request, Response
from flask.globals import g

# Some parts from http://flask.pocoo.org/snippets/8/

class Auth(object):
    
    def __init__(self, server):
        self.server = server
        
    @abc.abstractmethod
    def check_auth(self, username, password):
        pass

auth_obj = None

def set_auth(obj):
    global auth_obj
    auth_obj = obj
    
def authenticate():
    global auth_obj

    """Sends a 401 response that enables basic auth"""
    if auth_obj is None:
        return Response(
        'The chisubmit server does not have an authentication.\n'
        'mechanism configured. Please contact the server administrator', 500)
    else:
        return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})        

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from chisubmit.backend.webapp.api.users.models import User

        global auth_obj

        auth = request.authorization
        user = User.query.filter_by(id=unicode(auth.username)).first()

        if user is None:
            return authenticate()
        else:
            if not auth or not auth_obj or not auth_obj.check_auth(auth.username, auth.password):
                return authenticate()
            else:
                g.user = user
                return f(*args, **kwargs)
        
    return decorated    
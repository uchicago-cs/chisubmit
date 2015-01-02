from functools import wraps
from flask import request, abort, g
from chisubmit.backend.webapp.api.users.models import User


def require_apikey(view_function):
    @wraps(view_function)
    
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        api_key_param = request.args.get('api-key')
        api_key_header = request.headers.get("CHISUBMIT-API-KEY")
        
        if api_key_param is None and api_key_header is None:
            api_key = None
        else:
            if api_key_param is None:
                api_key = api_key_header
            else:
                api_key = api_key_param
            
        if api_key is not None:
            user = User.query.filter_by(api_key=api_key).first()
            
            if user is None:
                abort(401)
            else:
                g.user = user
                return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function
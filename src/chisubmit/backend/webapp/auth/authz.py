from functools import wraps
from flask import request, abort, g
from chisubmit.backend.webapp.api.people.models import Person


def require_admin_access(view_function):
    @wraps(view_function)
    
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        if g.user.admin:
            return view_function(*args, **kwargs)
        else:
            abort(403)

    return decorated_function

def check_admin_access_or_abort(person, status_code):
    if person.admin:
        return
    else:
        abort(status_code)

def check_course_access_or_abort(person, course, status_code):
    if person.admin:
        return
    
    if person.is_in_course(course):
        return
    else:
        abort(status_code)
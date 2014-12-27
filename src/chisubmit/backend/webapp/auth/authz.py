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

def check_roles(person, course, roles):
    if roles is None:
        return True
    else:
        if "student" in roles and person.is_student_in(course):
            return True
        elif "instructor" in roles and person.is_instructor_in(course):
            return True
        elif "grader" in roles and person.is_grader_in(course):
            return True
        else:
            return False
        

def check_admin_access_or_abort(person, status_code):
    if person.admin:
        return
    else:
        abort(status_code)

def check_course_access_or_abort(person, course, status_code, roles = None):
    if person.admin:
        return
    
    if not check_roles(person, course, roles):
        abort(status_code)
    
    if person.is_in_course(course):
        return
    else:
        abort(status_code)
        
def check_team_access_or_abort(person, team, status_code, roles = None):
    if person.admin:
        return
    
    course = team.course

    if not check_roles(person, course, roles):
        abort(status_code)
    
    if person.is_in_course(course):
        if person.is_instructor_in(course) or person.is_grader_in(course):
            return
        elif person.is_student_in(course) and person in team.students:
            return
        else:
            abort(status_code)
    else:
        abort(status_code)        
        
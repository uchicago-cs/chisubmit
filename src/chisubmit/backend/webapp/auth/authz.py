from functools import wraps
from flask import request, abort, g
from chisubmit.backend.webapp.api.users.models import User


def require_admin_access(view_function):
    @wraps(view_function)
    
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        if g.user.admin:
            return view_function(*args, **kwargs)
        else:
            abort(403)

    return decorated_function

def check_roles(user, course, roles):
    if roles is None:
        return True
    else:
        if "student" in roles and user.is_student_in(course):
            return True
        elif "instructor" in roles and user.is_instructor_in(course):
            return True
        elif "grader" in roles and user.is_grader_in(course):
            return True
        else:
            return False
        

def check_admin_access_or_abort(user, status_code):
    if user.admin:
        return
    else:
        abort(status_code)

def check_user_ids_equal_or_abort(user1_id, user2_id, status_code):
    if user1_id == user2_id:
        return
    else:
        abort(status_code)

def check_course_access_or_abort(user, course, status_code, roles = None):
    if user.admin:
        return
    
    if not check_roles(user, course, roles):
        abort(status_code)
    
    if user.is_in_course(course):
        return
    else:
        abort(status_code)
        
def check_team_access_or_abort(user, team, status_code, roles = None):
    if user.admin:
        return
    
    course = team.course

    if not check_roles(user, course, roles):
        abort(status_code)
    
    if user.is_in_course(course):
        if user.is_instructor_in(course) or user.is_grader_in(course):
            return
        elif user.is_student_in(course) and user in team.students:
            return
        else:
            abort(status_code)
    else:
        abort(status_code)        
        
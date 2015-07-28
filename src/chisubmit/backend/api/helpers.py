from django.http.response import Http404
from django.contrib.auth.models import User
from chisubmit.backend.api.models import Assignment, Team, TeamMember, Course,\
    CourseRoles, RubricComponent, Registration, Submission, Grade

def get_course(request, course_id):
    try:
        course_obj = Course.objects.get(course_id=course_id)
    except Course.DoesNotExist:
        raise Http404                           
    
    roles = course_obj.get_roles(request.user)
    
    if len(roles) == 0:
        raise Http404
    
    return course_obj, roles


def get_course_person(course_obj, request_user, roles, course_user_class, username):
    try:
        if len(roles) == 1 and CourseRoles.STUDENT in roles:
            if request_user.username != username:
                raise Http404
            
        user_obj = User.objects.get(username = username)
        person_obj = course_user_class.objects.get(course = course_obj, user = user_obj)
        return person_obj
    except User.DoesNotExist:
        raise Http404  
    except course_user_class.DoesNotExist:
        raise Http404 
    
def get_assignment(course_obj, request_user, roles, assignment_id):
    try:
        return Assignment.objects.get(course = course_obj, assignment_id = assignment_id)
    except Assignment.DoesNotExist:
        raise Http404  
    
def get_rubric_component(course_obj, request_user, roles, assignment_id, rubric_component_id):
    try:
        return RubricComponent.objects.get(assignment=assignment_id, pk=rubric_component_id)
    except RubricComponent.DoesNotExist:
        raise Http404      
    
def get_team(course_obj, request_user, roles, team_id):
    try:
        team_obj = Team.objects.get(course = course_obj, team_id = team_id)
        
        if len(roles) == 1 and CourseRoles.STUDENT in roles:
            if not team_obj.teammember_set.filter(student__user = request_user).exists():
                raise Http404
        
        return team_obj
    except Team.DoesNotExist:
        raise Http404
    
def get_team_member(course_obj, request_user, roles, team_id, student_username):
    try:
        team_obj = get_team(course_obj, request_user, roles, team_id)
        teammember_obj = TeamMember.objects.get(team = team_obj, student__user__username = student_username)
        return teammember_obj
    except (Team.DoesNotExist, TeamMember.DoesNotExist):
        raise Http404 
    
def get_registration(course_obj, request_user, roles, team_id, assignment_id):
    try:
        team_obj = get_team(course_obj, request_user, roles, team_id)
                
        if len(roles) == 1 and CourseRoles.STUDENT in roles:
            if not team_obj.teammember_set.filter(student__user = request_user).exists():
                raise Http404      
        
        registration_obj = Registration.objects.get(team = team_obj, assignment__assignment_id = assignment_id)
        return registration_obj
    except (Team.DoesNotExist, Registration.DoesNotExist):
        raise Http404         
    
def get_submission(course_obj, request_user, roles, team_id, assignment_id, submission_id):
    try:
        registration_obj = get_registration(course_obj, request_user, roles, team_id, assignment_id)
        submission_obj = Submission.objects.get(registration = registration_obj, pk = submission_id)
        
        return submission_obj
    except (Team.DoesNotExist, Registration.DoesNotExist, Submission.DoesNotExist):
        raise Http404       
    
def get_grade(course_obj, request_user, roles, team_id, assignment_id, grade_id):
    try:
        registration_obj = get_registration(course_obj, request_user, roles, team_id, assignment_id)
        grade_obj = Grade.objects.get(registration = registration_obj, pk = grade_id)
        
        return grade_obj
    except (Team.DoesNotExist, Registration.DoesNotExist, Grade.DoesNotExist):
        raise Http404                  
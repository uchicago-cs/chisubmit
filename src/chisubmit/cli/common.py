import click
import os.path
from functools import update_wrapper
from dateutil.parser import parse
import operator

from chisubmit.repos.grading import GradingGitRepo
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS,\
    ChisubmitException, handle_unexpected_exception
from chisubmit.client.exceptions import UnknownObjectException,\
    UnauthorizedException, BadRequestException, ChisubmitRequestException
from chisubmit.client.types import AttributeType
from requests.exceptions import ConnectionError, SSLError
from requests.packages.urllib3.exceptions import SSLError as SSLError_urllib3
from click.globals import get_current_context
from chisubmit.config import Config, ConfigDirectoryNotFoundException
from chisubmit.client import Chisubmit
from chisubmit.common.utils import parse_timedelta, convert_datetime_to_utc
from chisubmit.rubric import RubricFile, ChisubmitRubricException


def __load_config_and_client(require_local):
    ctx = get_current_context()
    
    try:
        ctx.obj["config"] = Config.get_config(ctx.obj["config_dir"], ctx.obj["work_dir"], ctx.obj["config_overrides"])
    except ConfigDirectoryNotFoundException:
        if not require_local:
            ctx.obj["config"] = Config.get_global_config(ctx.obj["config_overrides"])
        else:
            raise ChisubmitException("This command must be run in a directory configured to use chisubmit.")

    api_url = ctx.obj["config"].get_api_url()
    api_key = ctx.obj["config"].get_api_key()
    ssl_verify = ctx.obj["config"].get_ssl_verify()

    if api_url is None:
        raise ChisubmitException("Configuration value 'api-url' not found")

    if api_key is None:
        raise ChisubmitException("No chisubmit credentials were found!")

    ctx.obj["client"] = Chisubmit(api_key, base_url=api_url, ssl_verify=ssl_verify)    
    

def require_config(f):

    def new_func(*args, **kwargs):
        __load_config_and_client(require_local = False)
                
        return f(*args, **kwargs)

    return update_wrapper(new_func, f)


def require_local_config(f):
    
    def new_func(*args, **kwargs):
        __load_config_and_client(require_local = True)
                
        return f(*args, **kwargs)

    return update_wrapper(new_func, f)


def pass_course(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        course_id = ctx.obj["config"].get_course()

        if course_id is None:
            raise ChisubmitException("No course has been specified. Make sure you're in a directory configured "
                                     "to use chisubmit or, alternatively, use the '-c course=COURSE_ID' option.")
        else:
            try:
                course_obj = ctx.obj["client"].get_course(course_id = course_id)
            except UnknownObjectException:
                raise click.BadParameter("Course '%s' does not exist" % course_id)

            ctx.obj["course_obj"] = course_obj

            return ctx.invoke(f, ctx.obj["course_obj"], *args, **kwargs)

    return update_wrapper(new_func, f)


def catch_chisubmit_exceptions(f):
    
    def new_func(*args, **kwargs):
        ctx = get_current_context()
        try:
            return f(*args, **kwargs)
        except UnknownObjectException, uoe:
            print
            print "ERROR: There was an error processing this request"
            print
            print "URL: %s" % uoe.url
            print "HTTP method: %s" % uoe.method
            print "Error: Not found (404)"
            if ctx.obj["debug"]:
                print
                uoe.print_debug_info()
        except UnauthorizedException, ue:
            print
            print "ERROR: Your chisubmit credentials are invalid"
            print
            print "URL: %s" % ue.url
            print "HTTP method: %s" % ue.method
            print "Error: Unauthorized (401)"
            if ctx.obj["debug"]:
                print
                ue.print_debug_info()            
        except BadRequestException, bre:
            print
            print "ERROR: There was an error processing this request"
            print
            print "URL: %s" % bre.url
            print "HTTP method: %s" % bre.method
            print "Error(s):"
            bre.print_errors()
            if ctx.obj["debug"]:
                print
                bre.print_debug_info()
        except ChisubmitRequestException, cre:
            print "ERROR: chisubmit server returned an HTTP error"
            print
            print "URL: %s" % cre.url
            print "HTTP method: %s" % cre.method
            print "Status code: %i" % cre.status
            print "Message: %s" % cre.reason
            if ctx.obj["debug"]:
                print
                cre.print_debug_info()        
        except ConnectionError, ce:
            if isinstance(ce.message, (SSLError, SSLError_urllib3)):
                print "ERROR: SSL certificate error when connecting to server"                
            else:
                print "ERROR: Could not connect to server"
            print "URL: %s" % ce.request.url
            if ctx.obj["debug"]:
                print "Reason:", ce.message
        except ChisubmitException, ce:
            print "ERROR: %s" % ce
            if ctx.obj["debug"]:
                ce.print_exception()
        except click.UsageError:
            raise
        except Exception, e:
            handle_unexpected_exception()
            
        ctx.exit(CHISUBMIT_FAIL)
            
    return update_wrapper(new_func, f)


def get_course_or_exit(ctx, course_id):
    try:
        course = ctx.obj["client"].get_course(course_id = course_id)
        return course
    except UnknownObjectException:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    

def get_user_or_exit(ctx, username):
    try:
        user = ctx.obj["client"].get_user(username = username)
        return user
    except UnknownObjectException:
        print "User %s does not exist" % username
        ctx.exit(CHISUBMIT_FAIL)    

def get_assignment_or_exit(ctx, course, assignment_id, include_rubric = False):
    try:
        return course.get_assignment(assignment_id = assignment_id, include_rubric = include_rubric)
    except UnknownObjectException:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)
        
def get_team_or_exit(ctx, course, team_id):
    try:
        return course.get_team(team_id = team_id)
    except UnknownObjectException:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

def get_assignment_registration_or_exit(ctx, team, assignment_id):
    try:
        return team.get_assignment_registration(assignment_id = assignment_id)
    except UnknownObjectException:
        print "Team %s is not registered for assignment %s" % (team.team_id, assignment_id)
        ctx.exit(CHISUBMIT_FAIL)        
        
def get_instructor_or_exit(ctx, course, username):
    try:
        return course.get_instructor(username = username)
    except UnknownObjectException:
        print "Course %s does not have an instructor %s" % (course.course_id, username)
        ctx.exit(CHISUBMIT_FAIL)  
        
def get_grader_or_exit(ctx, course, username):
    try:
        return course.get_grader(username = username)
    except UnknownObjectException:
        print "Course %s does not have a grader %s" % (course.course_id, username)
        ctx.exit(CHISUBMIT_FAIL)  
        
def get_student_or_exit(ctx, course, username):
    try:
        return course.get_student(username = username)
    except UnknownObjectException:
        print "Course %s does not have a student %s" % (course.course_id, username)
        ctx.exit(CHISUBMIT_FAIL)             
        
        
def get_team_registration_from_user(ctx, course, assignment, user = None):
    if user is None:
        user = ctx.obj["client"].get_user()
        custom_user = False
    else:
        custom_user = True
    
    # Determine team for this assignment
    teams = course.get_teams(include_students=True, include_assignments=True)
    teams_registered_for_assignment = []
    for t in teams:
        if user.username not in [tm.username for tm in t.get_team_members()]:
            continue
        
        registrations = t.get_assignment_registrations()
        for r in registrations:
            if r.assignment_id == assignment.assignment_id:
                teams_registered_for_assignment.append((t,r))
                
    if len(teams_registered_for_assignment) == 0:
        if custom_user:
            print "%s is not registered for assignment %s" % (user.username, assignment.assignment_id)
        else:
            print "You are not registered for assignment %s" % assignment.assignment_id
        ctx.exit(CHISUBMIT_FAIL)        
    elif len(teams_registered_for_assignment) > 1:
        if custom_user:
            print "%s is registered for assignment %s in more than one team" % (user.username, assignment.assignment_id)
        else:
            print "You are registered for assignment %s in more than one team" % assignment.assignment_id
            print "Please notify your instructor about this."
        ctx.exit(CHISUBMIT_FAIL)        
        
    return teams_registered_for_assignment[0]                            


def api_obj_set_attribute(ctx, api_obj, attr_name, attr_value):
    valid_attrs = [attr for attr in api_obj._api_attributes.values() if attr.editable]
    valid_attrs_names = [attr.name for attr in valid_attrs]
    
    if attr_name not in valid_attrs_names:
        print "ERROR: '%s' is not a valid attribute." % attr_name
        print "Valid attributes are: %s" % (", ".join(valid_attrs_names))
        ctx.exit(CHISUBMIT_FAIL)
        
    attr = api_obj._api_attributes[attr_name]
    
    if attr.type.attrtype == AttributeType.STRING:
        v = attr_value
    elif attr.type.attrtype == AttributeType.INTEGER:
        v = int(attr_value)
    elif attr.type.attrtype == AttributeType.BOOLEAN:
        v = (attr_value in ("true", "True"))
    elif attr.type.attrtype == AttributeType.TIMEDELTA:
        v = parse_timedelta(attr_value)
    elif attr.type.attrtype == AttributeType.DATETIME:
        v = parse(attr_value)
        if v.tzinfo is None:
            v = convert_datetime_to_utc(v)
    else:
        print "ERROR: Editing attribute '%s' from the command-line is not currently supported." % attr_name
        ctx.exit(CHISUBMIT_FAIL)
        
    api_obj.edit(**{attr_name: v}) 


class DateTimeParamType(click.ParamType):
    name = 'datetime'

    def convert(self, value, param, ctx):
        try:
            return parse(value)
        except ValueError:
            self.fail('"%s" is not a valid datetime string' % value, param, ctx)

DATETIME = DateTimeParamType()


def get_teams_registrations(course, assignment, only_ready_for_grading=False, grader=None, only=None, include_grades=False):
    if only is not None:
        try:
            team = course.get_team(only, include_assignments=True, include_grades=include_grades)
            teams = [team]
        except UnknownObjectException:
            return {}
    else:
        teams = course.get_teams(include_assignments=True, include_grades=include_grades)

    rv = {}
    
    for team in teams:
        try:
            registrations = team.get_assignment_registrations()
            registration = [r for r in registrations if r.assignment_id == assignment.assignment_id]
            if len(registration) == 0:
                continue
            else:
                registration = registration[0]
            
            if (only_ready_for_grading and not registration.is_ready_for_grading()) or (grader is not None and registration.grader_username != grader.user.username):
                continue
            
            rv[team] = registration
        except UnknownObjectException:
            # Skip
            pass
        
    return rv


def create_grading_repos(config, course, assignment, teams_registrations, staging_only):
    repos = []

    teams = sorted(teams_registrations.keys(), key=operator.attrgetter("team_id"))

    for team in teams:
        registration = teams_registrations[team]
        repo = GradingGitRepo.get_grading_repo(config, course, team, registration)

        if repo is None:
            print ("Creating grading repo for %s... " % team.team_id),
            repo = GradingGitRepo.create_grading_repo(config, course, team, registration, staging_only)
            repo.sync()

            repos.append(repo)

            print "done"
        else:
            print "Grading repo for %s already exists" % team.team_id

    return repos


def gradingrepo_push_grading_branch(config, course, team, registration, to_students=False):
    repo = GradingGitRepo.get_grading_repo(config, course, team, registration)

    if repo is None:
        print "%s does not have a grading repository" % team.team_id
        return CHISUBMIT_FAIL
    
    if not repo.has_grading_branch():
        print "%s does not have a grading branch" % team.team_id
        return CHISUBMIT_FAIL

    if repo.is_dirty():
        print "Warning: %s grading repo has uncommitted changes." % team.team_id

    if to_students:
        repo.push_grading_branch_to_students()
    else:
        repo.push_grading_branch_to_staging()

    return CHISUBMIT_SUCCESS

def gradingrepo_pull_grading_branch(config, course, team, registration, from_students=False):
    repo = GradingGitRepo.get_grading_repo(config, course, team, registration)

    if repo is None:
        print "%s does not have a grading repository" % team.team_id
        return CHISUBMIT_FAIL

    if repo.is_dirty():
        print "%s grading repo has uncommited changes. Cannot pull." % team.team_id
        return CHISUBMIT_FAIL

    if from_students:
        if not repo.has_grading_branch_staging():
            print "%s does not have a grading branch on students' repository" % team.team_id
        else:
            repo.pull_grading_branch_from_students()
    else:
        if not repo.has_grading_branch_staging():
            print "%s does not have a grading branch in staging" % team.team_id
        else:
            repo.pull_grading_branch_from_staging()

    return CHISUBMIT_SUCCESS

def validate_repo_rubric(ctx, course, assignment, team, registration):
    repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, registration)
    if not repo:
        print "Repository for %s does not exist" % (team.team_id)
        ctx.exit(CHISUBMIT_FAIL)

    rubricfile = repo.repo_path + "/%s.rubric.txt" % assignment.assignment_id

    if not os.path.exists(rubricfile):
        print "Repository for %s does not exist have a rubric for assignment %s" % (team.team_id, assignment.assignment_id)
        ctx.exit(CHISUBMIT_FAIL)

    try:
        RubricFile.from_file(open(rubricfile), assignment)
        return (True, None)
    except ChisubmitRubricException, cre:
        return (False, cre.message)

def ask_yesno(prompt="Are you sure you want to continue? (y/n): ", yes=False):
        print prompt, 
        
        if not yes:
            yesno = raw_input()
        else:
            yesno = 'y'
            print 'y'
            
        return yesno in ('y', 'Y', 'yes', 'Yes', 'YES')    
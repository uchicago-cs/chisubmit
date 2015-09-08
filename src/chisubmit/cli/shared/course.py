import click
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.client.course import Course
from chisubmit.cli.common import pass_course, get_course_or_exit,\
    api_obj_set_attribute, get_instructor_or_exit, get_grader_or_exit,\
    get_student_or_exit, catch_chisubmit_exceptions, require_config,\
    require_local_config
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory


@click.command(name="list")
@catch_chisubmit_exceptions
@require_config
@click.pass_context
def shared_course_list(ctx):  
    courses = ctx.obj["client"].get_courses()
    
    for course in courses:
        print course.course_id, course.name

    return CHISUBMIT_SUCCESS


@click.command(name="get-git-credentials")
@click.option('--username', prompt='Enter your git username')
@click.option('--password', prompt='Enter your git password', hide_input=True)
@click.option('--no-save', is_flag=True)
@click.option('--delete-permissions', is_flag=True)
@click.option('--staging', is_flag=True)
@catch_chisubmit_exceptions
@pass_course
@click.pass_context
def shared_course_get_git_credentials(ctx, course, username, password, no_save, delete_permissions, staging):
    if not staging:
        connstr = course.git_server_connstr
    else:
        connstr = course.git_staging_connstr
    
    if connstr is None or connstr == "":
        print "Course '%s' doesn't seem to be configured to use a Git server." % course.id
        ctx.exit(CHISUBMIT_FAIL)
        
    conn = RemoteRepositoryConnectionFactory.create_connection(connstr, staging = staging)
    server_type = conn.get_server_type_name()

    token, existing = conn.get_credentials(username, password, delete_repo = delete_permissions)

    if token is None:
        print "Unable to create token. Incorrect username/password."
    else:
        if not no_save:
            if ctx.obj['config']['git-credentials'] is None:
                ctx.obj['config']['git-credentials'] = {}
            ctx.obj['config']['git-credentials'][server_type] = token
            ctx.obj['config'].save()
        
        if existing:
            print "Your existing %s access token is: %s" % (server_type, token)
        else:
            print "The following %s access token has been created: %s" % (server_type, token)

        if not no_save:
            print "chisubmit has been configured to use this token from now on."

    return CHISUBMIT_SUCCESS

@click.command(name="set-user-attribute")
@click.argument('user_type', type=click.Choice(["instructor", "grader", "student"]))
@click.argument('username', type=str)
@click.argument('attr_name', type=str)
@click.argument('attr_value', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def shared_course_set_user_attribute(ctx, course, user_type, username, attr_name, attr_value):
    if user_type == "instructor":
        user = get_instructor_or_exit(ctx, course, username)
    elif user_type == "grader":
        user = get_grader_or_exit(ctx, course, username)
    elif user_type == "student":
        user = get_student_or_exit(ctx, course, username)
    
    api_obj_set_attribute(ctx, user, attr_name, attr_value)

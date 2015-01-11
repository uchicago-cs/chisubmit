import click
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory
from chisubmit.common.utils import convert_datetime_to_utc, convert_datetime_to_local,\
    create_connection, get_datetime_now_utc
import pytz
from dateutil.parser import parse
from chisubmit.repos.github import GitHubConnection
import getpass
from chisubmit.cli.common import pass_course
from chisubmit.cli.shared.course import shared_course_list,\
    shared_course_set_default
from chisubmit.cli.shared.team import shared_team_list, shared_team_show

@click.group(name="course")
@click.pass_context
def student_course(ctx):
    pass


@click.command(name="get-git-credentials")
@click.option('--username', prompt='Enter your git username')
@click.option('--password', prompt='Enter your git password', hide_input=True)
@click.option('--no-save', is_flag=True)
@click.option('--delete-permissions', is_flag=True)
@pass_course
@click.pass_context
def student_course_get_git_credentials(ctx, course, username, password, no_save, delete_permissions):
    
    if not course.options.has_key("git-server-connstr"):
        print "Course '%s' doesn't seem to be configured to use a Git server." % course.id
        ctx.exit(CHISUBMIT_FAIL)
        
    connstr = course.options["git-server-connstr"]

    conn = RemoteRepositoryConnectionFactory.create_connection(connstr, staging = False)
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


@click.command(name="set-git-username")
@click.argument('username', type=str)
@pass_course
@click.pass_context
def student_course_set_git_username(ctx, course, username):
    course.set_student_repo_option(None, "git-username", username)

student_course.add_command(shared_course_list)
student_course.add_command(shared_course_set_default)

student_course.add_command(student_course_get_git_credentials)
student_course.add_command(student_course_set_git_username)


import click
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.client.course import Course
from chisubmit.cli.common import pass_course
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory


@click.command(name="list")
@click.pass_context
def shared_course_list(ctx):
    courses = Course.all()
    
    for course in courses:
        print course.id, course.name

    return CHISUBMIT_SUCCESS

@click.command(name="set-default")
@click.argument('course_id', type=str)
@click.pass_context
def shared_course_set_default(ctx, course_id):
    ctx.obj['config']['default-course'] = course_id
    ctx.obj['config'].save()

@click.command(name="get-git-credentials")
@click.option('--username', prompt='Enter your git username')
@click.option('--password', prompt='Enter your git password', hide_input=True)
@click.option('--no-save', is_flag=True)
@click.option('--delete-permissions', is_flag=True)
@click.option('--staging', is_flag=True)
@pass_course
@click.pass_context
def shared_course_get_git_credentials(ctx, course, username, password, no_save, delete_permissions, staging):
    if not staging:
        connstr_field = "git-server-connstr"
    else:
        connstr_field = "git-staging-connstr"
    
    if not course.options.has_key(connstr_field):
        print "Course '%s' doesn't seem to be configured to use a Git server." % course.id
        ctx.exit(CHISUBMIT_FAIL)
        
    connstr = course.options[connstr_field]

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

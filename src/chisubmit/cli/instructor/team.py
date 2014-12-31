import click
from chisubmit.cli.common import pass_course, DATETIME
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory


@click.group(name="team")
@click.pass_context
def instructor_team(ctx):
    pass

@click.command(name="repo-create")
@click.argument('team_id', type=str)
@click.option('--ignore-existing', is_flag=True)
@click.option('--public', is_flag=True)
@click.option('--staging', is_flag=True)
@pass_course
@click.pass_context
def instructor_team_repo_create(ctx, course, team_id, ignore_existing, public, staging):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL

    #if team.git_repo_created and not ignore_existing:
    #    print "Repository for team %s has already been created." % team.id
    #    print "Maybe you meant to run team-repo-update?"
    #    return CHISUBMIT_FAIL

    if not staging:
        connstr = course.options["git-server-connstr"]
        team_access = True
    else:
        connstr = course.options["git-staging-connstr"]
        team_access = False

    conn = RemoteRepositoryConnectionFactory.create_connection(connstr)
    server_type = conn.get_server_type_name()
    git_credentials = ctx.obj['config']['git-credentials'].get(server_type, None)

    if git_credentials is None:
        print "You do not have %s credentials." % server_type
        return CHISUBMIT_FAIL

    conn.connect(git_credentials)
    conn.create_team_repository(course, team, team_access, fail_if_exists = not ignore_existing, private = not public)

    return CHISUBMIT_SUCCESS


@click.command(name="repo-update")
@click.argument('team_id', type=str)
@pass_course
@click.pass_context
def instructor_team_repo_update(ctx, course, team_id):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL

    #if team.github_repo is None:
    #    print "Team %s does not have a repository." % team.id
    #    return CHISUBMIT_FAIL

    connstr = course.options["git-server-connstr"]

    conn = RemoteRepositoryConnectionFactory.create_connection(connstr)
    server_type = conn.get_server_type_name()
    git_credentials = ctx.obj['config']['git-credentials'].get(server_type, None)

    if git_credentials is None:
        print "You do not have %s credentials." % server_type
        return CHISUBMIT_FAIL

    conn.connect(git_credentials)
    conn.update_team_repository(team)
    return CHISUBMIT_SUCCESS


@click.command(name="repo-remove")
@click.argument('team_id', type=str)
@click.option('--staging', is_flag=True)
@pass_course
@click.pass_context
def instructor_team_repo_remove(ctx, course, team_id, staging):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL

    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL

    if not staging:
        connstr = course.options["git-server-connstr"]
    else:
        connstr = course.options["git-staging-connstr"]

    conn = RemoteRepositoryConnectionFactory.create_connection(connstr)
    server_type = conn.get_server_type_name()
    git_credentials = ctx.obj['config']['git-credentials'].get(server_type, None)

    if git_credentials is None:
        print "You do not have %s credentials." % server_type
        return CHISUBMIT_FAIL

    conn.connect(git_credentials)

    conn.delete_team_repository(team)

    return CHISUBMIT_SUCCESS


instructor_team.add_command(instructor_team_repo_create)
instructor_team.add_command(instructor_team_repo_update)
instructor_team.add_command(instructor_team_repo_remove)



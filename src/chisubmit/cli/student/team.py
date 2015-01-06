import click
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.common.utils import create_connection
from chisubmit.cli.common import pass_course
from chisubmit.cli.shared.team import shared_team_list, shared_team_show


@click.group(name="team")
@click.pass_context
def student_team(ctx):
    pass


@click.command(name="repo-check")
@click.argument('team_id', type=str)
@pass_course
@click.pass_context
def student_repo_check(ctx, course, team_id):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist or you do not have access to it" % team_id
        ctx.exit(CHISUBMIT_FAIL)
    
    #if not team.git_repo_created:
    #    print "Team %s does not have a repository." % team.id
    #    return CHISUBMIT_FAIL

    conn = create_connection(course, ctx.obj['config'])
    
    if conn is None:
        ctx.exit(CHISUBMIT_FAIL)

    if not conn.exists_team_repository(course, team):
        print "The repository for '%s' does not exist or you do not have permission to access it." % team_id
        ctx.exit(CHISUBMIT_FAIL)

    # TODO: Check that the user actually has push access
    print "Your repository exists and you have access to it."
    http_url = conn.get_repository_http_url(course, team)
    if http_url is not None:
        print "Repository website: %s" % conn.get_repository_http_url(course, team)
    print "Repository URL: %s" % conn.get_repository_git_url(course, team)

    return CHISUBMIT_SUCCESS

student_team.add_command(shared_team_list) 
student_team.add_command(shared_team_show)

student_team.add_command(student_repo_check)  

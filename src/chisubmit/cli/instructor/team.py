import click
from chisubmit.cli.common import pass_course, DATETIME
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory


@click.group(name="team")
@click.pass_context
def instructor_team(ctx):
    pass


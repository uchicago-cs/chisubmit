import click
from chisubmit.cli.admin.course import admin_course
from chisubmit.cli.admin.user import admin_user
from chisubmit.cli.common import get_access_token

@click.group()
@click.pass_context
def admin(ctx):
    pass

admin.add_command(get_access_token)

admin.add_command(admin_user)
admin.add_command(admin_course)

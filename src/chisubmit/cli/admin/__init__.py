import click
from chisubmit.cli.admin.course import admin_course
from chisubmit.cli.admin.user import admin_user

@click.group()
@click.pass_context
def admin(ctx):
    pass

admin.add_command(admin_user)
admin.add_command(admin_course)

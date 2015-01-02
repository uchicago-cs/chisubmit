import click
from chisubmit.cli.common import pass_course

@click.group(name="user")
@click.pass_context
def instructor_user(ctx):
    pass

@click.command(name="set-repo-option")
@click.argument('user_type', type=click.Choice(["instructor", "grader", "student"]))
@click.argument('user_id', type=str)
@click.argument('option', type=str)
@click.argument('value', type=str)
@pass_course
@click.pass_context
def instructor_user_set_repo_option(ctx, course, user_type, user_id, option, value):
    if user_type == "instructor":
        course.set_instructor_repo_option(user_id, option, value)
    elif user_type == "grader":
        course.set_grader_repo_option(user_id, option, value)
    elif user_type == "student":
        course.set_student_repo_option(user_id, option, value)


instructor_user.add_command(instructor_user_set_repo_option)


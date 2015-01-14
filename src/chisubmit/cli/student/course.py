import click
from chisubmit.cli.common import pass_course
from chisubmit.cli.shared.course import shared_course_list,\
    shared_course_set_default, shared_course_get_git_credentials

@click.group(name="course")
@click.pass_context
def student_course(ctx):
    pass




@click.command(name="set-git-username")
@click.argument('username', type=str)
@pass_course
@click.pass_context
def student_course_set_git_username(ctx, course, username):
    course.set_student_repo_option(None, "git-username", username)

student_course.add_command(shared_course_list)
student_course.add_command(shared_course_set_default)
student_course.add_command(student_course_set_git_username)
student_course.add_command(shared_course_get_git_credentials)


import click
from chisubmit.cli.shared.course import shared_course_list,\
    shared_course_set_default, shared_course_get_git_credentials

@click.group(name="course")
@click.pass_context
def instructor_course(ctx):
    pass

instructor_course.add_command(shared_course_list)
instructor_course.add_command(shared_course_set_default)
instructor_course.add_command(shared_course_get_git_credentials)


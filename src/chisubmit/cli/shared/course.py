import click
from chisubmit.common import CHISUBMIT_SUCCESS
from chisubmit.client.course import Course
from chisubmit.cli.common import pass_course


@click.command(name="list")
@click.pass_context
def shared_course_list(ctx):
    courses = Course.all()
    
    for course in courses:
        print course.id, course.name

    return CHISUBMIT_SUCCESS

@click.command(name="set-default")
@pass_course
@click.pass_context
def shared_course_set_default(ctx, course):
    ctx.obj['config']['default-course'] = course.id
    ctx.obj['config'].save()

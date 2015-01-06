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
@click.argument('course_id', type=str)
@click.pass_context
def shared_course_set_default(ctx, course_id):
    ctx.obj['config']['default-course'] = course_id
    ctx.obj['config'].save()

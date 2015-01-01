import click
from chisubmit.cli.common import pass_course, DATETIME
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS
from dateutil.parser import parse
from chisubmit.common.utils import convert_datetime_to_utc


@click.group(name="assignment")
@click.pass_context
def instructor_assignment(ctx):
    pass


@click.command(name="add")
@click.argument('assignment_id', type=str)
@click.argument('name', type=str)
@click.argument('deadline', type=DATETIME)
@pass_course
@click.pass_context
def instructor_assignment_add(ctx, course, assignment_id, name, deadline):
    deadline = convert_datetime_to_utc(deadline)
    
    assignment = Assignment(id = assignment_id,
                            name = name,
                            deadline = deadline,
                            course_id = course.id)
    
    return CHISUBMIT_SUCCESS

instructor_assignment.add_command(instructor_assignment_add)


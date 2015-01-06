import click
from chisubmit.cli.common import pass_course, DATETIME
from chisubmit.client.assignment import Assignment, GradeComponent
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from dateutil.parser import parse
from chisubmit.common.utils import convert_datetime_to_utc,\
    convert_datetime_to_local
import operator
from chisubmit.cli.shared.course import shared_course_list


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






@click.command(name="add-grade-component")
@click.argument('assignment_id', type=str)
@click.argument('grade_component_id', type=str)
@click.argument('description', type=str)
@click.argument('points', type=int)
@pass_course
@click.pass_context
def instructor_assignment_add_grade_component(ctx, course, assignment_id, grade_component_id, description, points):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    grade_component = GradeComponent(id = grade_component_id, description = description, points=points)
    assignment.add_grade_component(grade_component)

    return CHISUBMIT_SUCCESS


instructor_assignment.add_command(shared_course_list)

instructor_assignment.add_command(instructor_assignment_add)
instructor_assignment.add_command(instructor_assignment_add_grade_component)



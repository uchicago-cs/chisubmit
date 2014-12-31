import click
from chisubmit.cli.common import pass_course
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS

@click.group()
@click.pass_context
def student(ctx):
    pass


@click.command(name="register-for-assignment")
@click.argument('assignment_id', type=str)
@click.option('--team-name', type=str)
@click.option('--partner', type=str, multiple=True)
@pass_course
@click.pass_context
def student_assignment_register(ctx, course, assignment_id, team_name, partner):
    a = Assignment.from_course_and_id(course.id, assignment_id)
        
    a.register(team_name = team_name,
               partners = partner)
    
    return CHISUBMIT_SUCCESS

student.add_command(student_assignment_register)
import click
from chisubmit.cli.student.assignment import student_assignment
from chisubmit.cli.student.team import student_team
from chisubmit.cli.student.course import student_course

@click.group()
@click.pass_context
def student(ctx):
    pass

student.add_command(student_assignment)
student.add_command(student_course)
student.add_command(student_team)

    





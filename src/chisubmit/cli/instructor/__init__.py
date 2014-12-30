import click
from chisubmit.cli.instructor.assignment import instructor_assignment

@click.group()
@click.pass_context
def instructor(ctx):
    pass

instructor.add_command(instructor_assignment)
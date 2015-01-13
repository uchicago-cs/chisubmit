import click
from chisubmit.cli.common import pass_course
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS

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


@click.command(name="student-set-dropped")
@click.argument('student_id', type=str)
@pass_course
@click.pass_context
def instructor_student_set_dropped(ctx, course, student_id):
    student = course.get_student(student_id)
    if student is None:
        print "Student %s does not exist" % student_id
        ctx.exit(CHISUBMIT_FAIL)

    course.set_student_dropped(student_id)

    return CHISUBMIT_SUCCESS

@click.command(name="grader-add-conflict")
@click.argument('grader_id', type=str)
@click.argument('student_id', type=str)
@pass_course
@click.pass_context
def instructor_grader_add_conflict(ctx, course, grader_id, student_id):
    grader = course.get_grader(grader_id)
    if grader is None:
        print "Grader %s does not exist" % grader_id
        ctx.exit(CHISUBMIT_FAIL)

    student = course.get_student(student_id)
    if student is None:
        print "Student %s does not exist" % student_id
        ctx.exit(CHISUBMIT_FAIL)

    course.add_grader_conflict(grader, student_id)

    return CHISUBMIT_SUCCESS


instructor_user.add_command(instructor_user_set_repo_option)
instructor_user.add_command(instructor_student_set_dropped)
instructor_user.add_command(instructor_grader_add_conflict)


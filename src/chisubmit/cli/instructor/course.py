import click
from chisubmit.cli.common import pass_course, catch_chisubmit_exceptions,\
    require_local_config
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS
from chisubmit.cli.shared.course import shared_course_set_user_attribute,\
    shared_course_get_git_credentials, shared_course_list
    
@click.group(name="course")
@click.pass_context
def instructor_course(ctx):
    pass

@click.command(name="grader-add-conflict")
@click.argument('grader_id', type=str)
@click.argument('student_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
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

instructor_course.add_command(shared_course_list)
instructor_course.add_command(shared_course_set_user_attribute)
instructor_course.add_command(shared_course_get_git_credentials)


import click
from chisubmit.cli.common import pass_course, get_student_or_exit,\
    api_obj_set_attribute, catch_chisubmit_exceptions, require_local_config
from chisubmit.cli.shared.course import shared_course_list,\
    shared_course_get_git_credentials

@click.group(name="course")
@click.pass_context
def student_course(ctx):
    pass

@click.command(name="set-git-username")
@click.argument('git-username', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def student_course_set_git_username(ctx, course, git_username):
    user = ctx.obj["client"].get_user()
    
    student = get_student_or_exit(ctx, course, user.username)
    
    api_obj_set_attribute(ctx, student, "git_username", git_username)    
    

student_course.add_command(shared_course_list)
student_course.add_command(student_course_set_git_username)
student_course.add_command(shared_course_get_git_credentials)


import click
from chisubmit.cli.common import pass_course, get_student_or_exit,\
    api_obj_set_attribute, catch_chisubmit_exceptions, require_local_config
from chisubmit.cli.shared.course import shared_course_list,\
    shared_course_get_git_credentials
from chisubmit.client.exceptions import UnknownObjectException
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS

@click.group(name="course")
@click.pass_context
def student_course(ctx):
    pass

@click.command(name="show-extensions")
@click.option('--username', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def student_course_show_extensions(ctx, course, username):
    user = ctx.obj["client"].get_user()
    
    if username is not None:
        try:
            course.get_instructor(user.username)
        except UnknownObjectException:
            print "Only instructors can use the --username option"
            ctx.exit(CHISUBMIT_FAIL)
    else:
        username = user.username
   
    student = get_student_or_exit(ctx, course, username)
    
    if course.extension_policy == "per-team":
        print "This course uses per-team extensions."
        print "Please use 'chisubmit student team show' to see the number of extensions"
        print "available for the teams you are in."
        ctx.exit(CHISUBMIT_SUCCESS)
        
    print "%s, %s" % (student.user.last_name, student.user.first_name) 
    print
    teams = course.get_teams()
    
    extensions = student.extensions
    extensions_used = []
    
    for t in teams:
        if username not in [tm.username for tm in t.get_team_members()]:
            continue
        
        registrations = t.get_assignment_registrations()
        for reg in registrations:
            if reg.final_submission is not None:
                ex = reg.final_submission.extensions_used
                if ex > 0:
                    extensions_used.append((reg.assignment_id, t.team_id, ex))
                    
    n_extensions_used = sum([x[2] for x in extensions_used])
                    
    print "You started with %i extensions and you have %i extensions left." % (extensions, extensions - n_extensions_used)
    
    if len(extensions_used) > 0:
        for aid, tid, ex in extensions_used:
            print "- You used %i extension(s) on %s (as '%s')" % (ex, aid, tid)
                
    
        

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
student_course.add_command(student_course_show_extensions)
student_course.add_command(student_course_set_git_username)
student_course.add_command(shared_course_get_git_credentials)


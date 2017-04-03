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

@click.command(name="update-students-extensions")
@click.argument('extensions', type=int)
@click.option('--relative', is_flag=True)
@click.option('--print-student-ids', is_flag=True)
@click.option('--only', type=str)
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_update_students_extensions(ctx, course, extensions, print_student_ids, relative, only, yes):
    if only is not None:
        student = course.get_student(only)
        if student is None:
            print "Student %s does not exist" % only
            ctx.exit(CHISUBMIT_FAIL)
        students = [student]
    else:
        students = [s for s in course.get_students() if not s.dropped]

    if not relative and extensions < 0:
        print "Must specify a number of extensions greater than or equal to zero."
        
    changes = {}
    for s in students:
        ext_cur = s.extensions
        if relative:
            ext_new = ext_cur + extensions
        else:
            ext_new = extensions
            
        changes.setdefault((ext_cur, ext_new), []).append(s)
        
    print "The following changes will be made:"
    
    for (ext_cur, ext_new) in changes:
        st = changes[(ext_cur, ext_new)]
        if ext_cur == ext_new:
            change = " (NO CHANGE)"
        else:
            change = ""
        print " - %i students: %i extensions -> %i extensions%s" % (len(st), ext_cur, ext_new, change)
        if print_student_ids:
            print "   " + ", ".join([s.username for s in st])
        print
        
    print "Are you sure you want to proceed? (y/n): ", 
        
    if not yes:
        yesno = raw_input()
    else:
        yesno = 'y'
        print 'y'

    if yesno not in ('y', 'Y', 'yes', 'Yes', 'YES'):
        ctx.exit(CHISUBMIT_FAIL)        
        
    for (ext_cur, ext_new) in changes:
        st = changes[(ext_cur, ext_new)]
        for s in st:
            s.extensions = ext_new    

    return CHISUBMIT_SUCCESS


instructor_course.add_command(shared_course_list)
instructor_course.add_command(shared_course_set_user_attribute)
instructor_course.add_command(shared_course_get_git_credentials)
instructor_course.add_command(instructor_update_students_extensions)




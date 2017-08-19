import click
from chisubmit.cli.common import pass_course, DATETIME, get_assignment_or_exit,\
    catch_chisubmit_exceptions, require_local_config, get_team_or_exit,\
    get_assignment_registration_or_exit, ask_yesno
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.common.utils import convert_datetime_to_utc, create_connection,\
    convert_datetime_to_local, is_submission_ready_for_grading
import operator
from chisubmit.cli.shared.assignment import shared_assignment_list,\
    shared_assignment_set_attribute
from chisubmit.client.exceptions import UnknownObjectException,\
    BadRequestException
from chisubmit.cli.student.assignment import print_commit
from chisubmit.rubric import RubricFile, ChisubmitRubricException


@click.group(name="assignment")
@click.pass_context
def instructor_assignment(ctx):
    pass


@click.command(name="add")
@click.argument('assignment_id', type=str)
@click.argument('name', type=str)
@click.argument('deadline', type=DATETIME)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_assignment_add(ctx, course, assignment_id, name, deadline):
    deadline = convert_datetime_to_utc(deadline)
    
    course.create_assignment(assignment_id, name, deadline)
    
    return CHISUBMIT_SUCCESS


@click.command(name="add-rubric")
@click.argument('assignment_id', type=str)
@click.argument('rubric_file', type=click.File('r'))
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_assignment_add_rubric(ctx, course, assignment_id, rubric_file, yes):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    try:
        rubric = RubricFile.from_file(rubric_file) 
    except ChisubmitRubricException, cre:
        print "ERROR: Rubric does not validate (%s)" % (cre.message)
        return CHISUBMIT_FAIL    
    
    rubric_components = assignment.get_rubric_components()

    if len(rubric_components) > 0:
        print "This assignment already has a rubric. If you load this"
        print "new rubric, the old one will be REMOVED. If grading of"
        print "this assignment has already begun, doing this may break"
        print "existing rubric files completed by the graders."
        print
        if not ask_yesno(yes=yes):
            return CHISUBMIT_FAIL
        print
        for rc in rubric_components:
            rc.delete()
    
    order = 10
    for rc in rubric.rubric_components:
        points = rubric.points_possible[rc]
        assignment.create_rubric_component(rc, points, order)
        order += 10

    return CHISUBMIT_SUCCESS

@click.command(name="update-rubric")
@click.argument('assignment_id', type=str)
@click.argument('rubric_component', type=str)
@click.option('--description', type=str)
@click.option('--points', type=float)
@click.option('--add', is_flag=True)
@click.option('--edit', is_flag=True)
@click.option('--remove', is_flag=True)
@click.option('--up', is_flag=True)
@click.option('--down', is_flag=True)
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_assignment_update_rubric(ctx, course, assignment_id, rubric_component, description, points, add, edit, remove, up, down, yes):
    num_cmds = len([x for x in [add,edit,remove,up,down] if x is True])
    if num_cmds > 1:
        print "You can only specify one of the following: --add / --edit / --remove / --up / --down"
        return CHISUBMIT_FAIL
    if num_cmds == 0:
        print "You must specify one of the following: --add / --edit / --remove / --up / --down"
        return CHISUBMIT_FAIL
    if add and points is None:
        print "The --add option requires the --points option"
        return CHISUBMIT_FAIL
    if edit and not (description or points):
        print "The --edit option requires the --description option or the --points option (or both)"
        return CHISUBMIT_FAIL
    if (remove or up or down) and points is not None:
        print "The --points option cannot be used with --remove/--up/--down"        
        return CHISUBMIT_FAIL
    if (remove or up or down) and points is not None:
        print "The --points option cannot be used with --remove/--up/--down"        
        return CHISUBMIT_FAIL
    
    assignment = get_assignment_or_exit(ctx, course, assignment_id)
  
    rubric_components = assignment.get_rubric_components()
    
    rcs = [(i, rc) for i, rc in enumerate(rubric_components) if rc.description == rubric_component]
    if len(rcs) == 0:
        if not add:
            print "No such rubric component: %s" % rubric_component
            return CHISUBMIT_FAIL
        else:
            i, rc = None, None
    elif len(rcs) > 1:
        print "Multiple rubric components with this name: %s" % rubric_component
        print "(this should not happen)"
        return CHISUBMIT_FAIL            
    else:
        i, rc = rcs[0]
    
    if add:
        if rc is not None:
            print "There is already a rubric component with this name: %s" % rubric_component
            return CHISUBMIT_FAIL
        
        if len(rubric_components) == 0:
            last_order = 0
        else:
            last_order = rubric_components[-1].order

        assignment.create_rubric_component(rubric_component, points, last_order + 10)
    elif edit:
        if description is not None:
            print "If grading of this assignment has begun, changing the"
            print "description of a rubric component may break existing"
            print "rubric files completed by the graders."
            print
            if not ask_yesno(yes=yes):
                return CHISUBMIT_FAIL
            print            
            rc.description = description
        if points is not None:
            rc.points = points
    elif remove:
        print "If grading of this assignment has begun, removing"
        print "a rubric component may break existing rubric files"
        print "completed by the graders."
        print
        if not ask_yesno(yes=yes):
            return CHISUBMIT_FAIL
        print            
        rc.delete()   
    elif up:
        if i-1 >= 0:
            other_rc = rubric_components[i-1]
            other_rc_order = rubric_components[i-1].order
            
            other_rc.order = rc.order
            rc.order = other_rc_order
    elif down:
        if i+1 < len(rubric_components):
            other_rc = rubric_components[i+1]
            other_rc_order = rubric_components[i+1].order
            
            other_rc.order = rc.order
            rc.order = other_rc_order       


@click.command(name="show-rubric")
@click.argument('assignment_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_assignment_show_rubric(ctx, course, assignment_id):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    rubric = RubricFile.from_assignment(assignment)
    print(rubric.to_yaml())


@click.command(name="register")
@click.argument('assignment_id', type=str)
@click.option('--student', type=str, multiple=True)
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_assignment_register(ctx, course, assignment_id, student, yes):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)
    
    if len(student) < assignment.min_students or len(student) > assignment.max_students:
        print "You specified %i students, but this assignment requires teams with at least %i students and at most %i students" % (len(student), assignment.min_students, assignment.max_students)
        print
        print "Are you sure you want to proceed? (y/n): ", 
        
        if not yes:
            yesno = raw_input()
        else:
            yesno = 'y'
            print 'y'
    
        if yesno not in ('y', 'Y', 'yes', 'Yes', 'YES'):
            ctx.exit(CHISUBMIT_FAIL)

    assignment.register(students = student)
    
    print "Registration successful."
    
    return CHISUBMIT_SUCCESS


@click.command(name="submit")
@click.argument('team_id', type=str)    
@click.argument('assignment_id', type=str)
@click.argument('commit_sha', type=str)
@click.argument('extensions', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context  
def instructor_assignment_submit(ctx, course, team_id, assignment_id, commit_sha, extensions):
    team = get_team_or_exit(ctx, course, team_id)
    registration = get_assignment_registration_or_exit(ctx, team, assignment_id)
            
    conn = create_connection(course, ctx.obj['config'])
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)
    
    commit = conn.get_commit(course, team, commit_sha)
    
    if commit is None:
        print "Commit %s does not exist in repository" % commit_sha
        ctx.exit(CHISUBMIT_FAIL)
    
    if registration.final_submission is not None:
        prior_commit_sha = registration.final_submission.commit_sha
        prior_submitted_at_utc = registration.final_submission.submitted_at
        prior_submitted_at_local = convert_datetime_to_local(prior_submitted_at_utc)            
        
        submission_commit = conn.get_commit(course, team, prior_commit_sha)            
        
        if prior_commit_sha == commit_sha:
            print "The team has already submitted assignment %s" % registration.assignment.assignment_id
            print "They submitted the following commit on %s:" % prior_submitted_at_local
            print
            if submission_commit is None:
                print "WARNING: Previously submitted commit '%s' is not in the repository!" % prior_commit_sha
            else:
                print_commit(submission_commit)
            print
            print "You are trying to submit the same commit again (%s)" % prior_commit_sha
            print "If you want to re-submit, please specify a different commit"
            ctx.exit(CHISUBMIT_FAIL)
            
        print
        print "WARNING: This team has already submitted assignment %s and you" % registration.assignment.assignment_id 
        print "are about to overwrite the previous submission of the following commit:"
        print
        if submission_commit is None:
            print "WARNING: Previously submitted commit '%s' is not in the repository!" % prior_commit_sha
        else:
            print_commit(submission_commit)
        print

    if registration.final_submission is not None:
        msg = "THE ABOVE SUBMISSION FOR %s (%s) WILL BE CANCELLED." % (registration.assignment.assignment_id, registration.assignment.name)
        
        print "!"*len(msg)
        print msg
        print "!"*len(msg)
        print
        print "If you continue, their submission for %s (%s)" % (registration.assignment.assignment_id, registration.assignment.name)
        print "will now point to the following commit:"                
    else:
        print "You are going to make a submission for %s (%s)." % (registration.assignment.assignment_id, registration.assignment.name)
        print "The commit you are submitting is the following:"
    print
    print_commit(commit)
    print
    print "PLEASE VERIFY THIS IS THE EXACT COMMIT YOU WANT TO SUBMIT"
    print
    print "Are you sure you want to continue? (y/n): ", 
    
    yesno = raw_input()
    
    if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):
        try:
            submit_response = registration.submit(commit_sha, extensions_override = extensions, dry_run=False)
                        
            print "The submission has been completed."
            return CHISUBMIT_SUCCESS

        except BadRequestException, bre:        
            print "ERROR: The submission was not completed. The server reported the following errors:"
            bre.print_errors()
            return CHISUBMIT_FAIL        


@click.command(name="cancel-submit")   
@click.argument('team_id', type=str)    
@click.argument('assignment_id', type=str)
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context  
def instructor_assignment_cancel_submit(ctx, course, team_id, assignment_id, yes):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)
    team = get_team_or_exit(ctx, course, team_id)
    registration = get_assignment_registration_or_exit(ctx, team, assignment.assignment_id)
        
    if registration.final_submission is None:
        print "Team %s has not made a submission for assignment %s," % (team.team_id, assignment_id)
        print "so there is nothing to cancel."
        ctx.exit(CHISUBMIT_FAIL)
        
    if registration.grader_username is not None:
        print "This submission has already been assigned a grader (%s)" % registration.grader_username
        print "Make sure the grader has been notified to discard this submission."
        print "You must also remove the existing grading branch from the staging server."
        
        print "Are you sure you want to proceed? (y/n): ", 
        
        if not yes:
            yesno = raw_input()
        else:
            yesno = 'y'
            print 'y'
        
        if yesno not in ('y', 'Y', 'yes', 'Yes', 'YES'):
            ctx.exit(CHISUBMIT_FAIL)
        else:
            print
        
    if is_submission_ready_for_grading(assignment_deadline=registration.assignment.deadline, 
                                       submission_date=registration.final_submission.submitted_at,
                                       extensions_used=registration.final_submission.extensions_used):
        print "WARNING: You are canceling a submission that is ready for grading!"
            
    conn = create_connection(course, ctx.obj['config'])
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)
        
    submission_commit = conn.get_commit(course, team, registration.final_submission.commit_sha)
        
    print
    print "This is the existing submission for assignment %s:" % assignment_id
    print
    if submission_commit is None:
        print "WARNING: Previously submitted commit '%s' is not in the repository!" % registration.final_submission.commit_sha
    else:
        print_commit(submission_commit)
    print    

    print "Are you sure you want to cancel this submission? (y/n): ", 
    
    if not yes:
        yesno = raw_input()
    else:
        yesno = 'y'
        print 'y'
    
    if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):
        registration.final_submission_id = None
        registration.grader_username = None
        
        print
        print "The submission has been cancelled."


@click.command(name="stats")
@click.argument('assignment_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_assignment_stats(ctx, course, assignment_id):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)
             
    all_students = course.get_students()
         
    student_dict = {s.user.username: s.user for s in all_students if not s.dropped}
    students = set(student_dict.keys())
    dropped = set([s.user.username for s in all_students if s.dropped])
    
    teams_unconfirmed = []
    nteams = 0
    nstudents = len(student_dict)
    nstudents_assignment = 0
    nsubmissions = 0
    nstudents_submitted = 0
    unsubmitted = []
    
    teams = course.get_teams(include_students=True, include_assignments=True)

    for team in teams:
        try:
            registrations = team.get_assignment_registrations()
            registrations = [r for r in registrations if r.assignment_id == assignment_id]
            if len(registrations) == 1:
                registration = registrations[0]
            else:
                continue
        except UnknownObjectException:
            continue
        
        unconfirmed = False
        includes_dropped = False
        team_members = team.get_team_members()
        for tm in team_members:
            if tm.username not in dropped:
                try:
                    students.remove(tm.username)
                    nstudents_assignment += 1
                    if not tm.confirmed:
                        unconfirmed = True
                except KeyError, ke:
                    print "WARNING: Student %s seems to be in more than one team (offending team: %s)" % (tm.username, team.team_id)
            else:
                includes_dropped = True

        if not includes_dropped:
            nteams += 1
            
            if registration.final_submission is not None:
                nsubmissions += 1
                nstudents_submitted += len(team_members)
            else:
                unsubmitted.append(team)
            
        if unconfirmed:
            teams_unconfirmed.append(team)
                
    assert(nstudents == len(students) + nstudents_assignment)                
            
    title = "Assignment '%s'" % (assignment.name)
    print title
    print "=" * len(title)
               
    print 
    print "%i / %i students in %i teams have signed up for assignment %s" % (nstudents_assignment, nstudents, nteams, assignment.assignment_id)
    print
    print "%i / %i teams have submitted the assignment (%i students)" % (nsubmissions, nteams, nstudents_submitted)
    
    if ctx.obj["verbose"]:
        if len(students) > 0:
            print
            print "Students who have not yet signed up"
            print "-----------------------------------"
            not_signed_up = [student_dict[sid] for sid in students]
            not_signed_up.sort(key=operator.attrgetter("last_name"))
            for s in not_signed_up:
                print "%s, %s <%s>" % (s.last_name, s.first_name, s.email)
                
        if len(unsubmitted) > 0:
            print
            print "Teams that have not submitted"
            print "-----------------------------"
            for t in unsubmitted:
                print t.team_id
                
    return CHISUBMIT_SUCCESS


instructor_assignment.add_command(shared_assignment_list)
instructor_assignment.add_command(shared_assignment_set_attribute)

instructor_assignment.add_command(instructor_assignment_add)
instructor_assignment.add_command(instructor_assignment_add_rubric)
instructor_assignment.add_command(instructor_assignment_update_rubric)
instructor_assignment.add_command(instructor_assignment_show_rubric)
instructor_assignment.add_command(instructor_assignment_register)
instructor_assignment.add_command(instructor_assignment_submit)
instructor_assignment.add_command(instructor_assignment_cancel_submit)
instructor_assignment.add_command(instructor_assignment_stats)


import click
from chisubmit.cli.common import pass_course, DATETIME, get_assignment_or_exit,\
    catch_chisubmit_exceptions, require_local_config, get_team_or_exit,\
    get_assignment_registration_or_exit
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.common.utils import convert_datetime_to_utc, create_connection,\
    convert_datetime_to_local
import operator
from chisubmit.cli.shared.assignment import shared_assignment_list,\
    shared_assignment_set_attribute
from chisubmit.client.exceptions import UnknownObjectException,\
    BadRequestException
from chisubmit.cli.student.assignment import print_commit


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


@click.command(name="add-rubric-component")
@click.argument('assignment_id', type=str)
@click.argument('description', type=str)
@click.argument('points', type=float)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_assignment_add_rubric_component(ctx, course, assignment_id, description, points):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)
    assignment.create_rubric_component(description, points)

    return CHISUBMIT_SUCCESS


@click.command(name="register")
@click.argument('assignment_id', type=str)
@click.option('--student', type=str, multiple=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_assignment_register(ctx, course, assignment_id, student):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)
    
    assignment.register(students = student)
    
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
instructor_assignment.add_command(instructor_assignment_add_rubric_component)
instructor_assignment.add_command(instructor_assignment_register)
instructor_assignment.add_command(instructor_assignment_submit)
instructor_assignment.add_command(instructor_assignment_stats)


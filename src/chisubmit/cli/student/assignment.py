import click
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.common.utils import convert_datetime_to_local,\
    create_connection, get_datetime_now_utc, compute_extensions_needed,\
    is_submission_ready_for_grading
from dateutil.parser import parse
from chisubmit.cli.common import pass_course, get_assignment_or_exit,\
    get_team_or_exit, get_assignment_registration_or_exit,\
    catch_chisubmit_exceptions, require_local_config
from chisubmit.cli.shared.assignment import shared_assignment_list
from datetime import timedelta
from chisubmit.client.exceptions import BadRequestException,\
    UnknownObjectException


@click.group(name="assignment")
@click.pass_context
def student_assignment(ctx):
    pass


@click.command(name="register")
@click.argument('assignment_id', type=str)
@click.option('--partner', type=str, multiple=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def student_assignment_register(ctx, course, assignment_id, partner):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)
    
    user = ctx.obj["client"].get_user()
    
    try:
        course.get_instructor(user.username)
        
        # If get_instructor doesn't raise an exception, then the user
        # is an instructor, and we don't include the user in the list
        # of partners.
        r = assignment.register(students = partner)    
    except UnknownObjectException:
        # Otherwise, we include the current user
        r = assignment.register(students = partner + (user.username,))    

    print "Your registration for %s (%s) is complete." % (r.registration.assignment.assignment_id, r.registration.assignment.name)
    
    if len(r.team_members) > 1:
        some_unconfirmed = False
        print 
        print "Your team name is '%s'." % r.team.team_id
        print
        print "The team is composed of the following students:"
        print
        for tm in r.team_members:
            if tm.confirmed:
                conf = ""
            else:
                conf = "UNCONFIRMED"
                some_unconfirmed = True
                
            print " - %s, %s (%s) %s" % (tm.student.user.last_name, 
                                         tm.student.user.first_name,
                                         tm.student.user.username,
                                         conf)
             
            if some_unconfirmed:
                print
                print "Note: Some students have not yet confirmed that they are part of"
                print "      this team. To confirm they are part of this team, they just"
                print "      need to register as a team themselves (using this same"
                print "      command, and listing the same team members)."
    
    return CHISUBMIT_SUCCESS

@click.command(name="show-deadline")
@click.argument('assignment_id', type=str)
@click.option('--utc', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def student_assignment_show_deadline(ctx, course, assignment_id, utc):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    now_utc = get_datetime_now_utc()
    now_local = convert_datetime_to_local(now_utc)

    deadline_utc = assignment.deadline
    deadline_local = convert_datetime_to_local(deadline_utc)

    print assignment.name
    print
    if utc:
        print "      Now (Local): %s" % now_local.isoformat(" ")
        print " Deadline (Local): %s" % deadline_local.isoformat(" ")
        print
        print "        Now (UTC): %s" % now_utc.isoformat(" ")
        print "   Deadline (UTC): %s" % deadline_utc.isoformat(" ")
    else:
        print "      Now: %s" % now_local.isoformat(" ")
        print " Deadline: %s" % deadline_local.isoformat(" ")

    print

    extensions = compute_extensions_needed(now_utc, deadline_utc)

    if extensions == 0:
        diff = deadline_utc - now_utc
    else:
        diff = now_utc - deadline_utc

    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds//60)%60
    seconds = diff.seconds%60

    if extensions == 0:
        print "The deadline has not yet passed"
        print "You have %i days, %i hours, %i minutes, %i seconds left" % (days, hours, minutes, seconds)
    else:
        print "The deadline passed %i days, %i hours, %i minutes, %i seconds ago" % (days, hours, minutes, seconds)
        print "If you submit your assignment now, you will need to use %i extensions" % extensions

    return CHISUBMIT_SUCCESS


def print_commit(commit):
    print "      Commit: %s" % commit.sha
    print "        Date: %s" % commit.committed_date.isoformat(sep=" ")
    print "     Message: %s" % commit.message
    print "      Author: %s <%s>" % (commit.author_name, commit.author_email)        


@click.command(name="submit")
@click.argument('team_id', type=str)    
@click.argument('assignment_id', type=str)
@click.argument('commit_sha', type=str)
@click.option('--extensions', type=int, default=0)
@click.option('--force', is_flag=True)
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context  
def student_assignment_submit(ctx, course, team_id, assignment_id, commit_sha, extensions, force, yes):
    team = get_team_or_exit(ctx, course, team_id)
    registration = get_assignment_registration_or_exit(ctx, team, assignment_id)
    
    if registration.final_submission is not None:
        if is_submission_ready_for_grading(assignment_deadline=registration.assignment.deadline, 
                                           submission_date=registration.final_submission.submitted_at,
                                           extensions_used=registration.final_submission.extensions_used):
            print "You cannot re-submit this assignment."
            print "You made a submission before the deadline, and the deadline has passed."
    
            ctx.exit(CHISUBMIT_FAIL)
        
    conn = create_connection(course, ctx.obj['config'])
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)
    
    commit = conn.get_commit(course, team, commit_sha)
    
    if commit is None:
        print "Commit %s does not exist in repository" % commit_sha
        ctx.exit(CHISUBMIT_FAIL)

    try:
        submit_response = registration.submit(commit_sha, extensions, dry_run=True)
    except BadRequestException, bre:
        response_data = bre.json
        extensions_needed = response_data["extensions_needed"]
        extensions_available = response_data["extensions_available"]
        
        deadline_utc = parse(response_data["deadline"])
        submitted_at_utc = parse(response_data["submitted_at"])
        deadline_local = convert_datetime_to_local(deadline_utc)
        submitted_at_local = convert_datetime_to_local(submitted_at_utc)        
        
        if extensions_needed > extensions_available:
            msg1 = "You do not have enough extensions to submit this assignment."
            msg2 = "You would need %i extensions to submit this assignment at this " \
                   "time, but you only have %i left" % (extensions_needed, extensions_available)
        elif extensions < extensions_needed:
            msg1 = "The number of extensions you have requested is insufficient."
            msg2 = "You need to request %s extensions." % extensions_needed
        elif extensions > extensions_needed:
            msg1 = "The number of extensions you have requested is excessive."
            msg2 = "You only need to request %s extensions." % extensions_needed

        print
        print msg1
        print            
        print "     Deadline (UTC): %s" % deadline_utc.isoformat(sep=" ")
        print "          Now (UTC): %s" % submitted_at_utc.isoformat(sep=" ")
        print 
        print "   Deadline (Local): %s" % deadline_local.isoformat(sep=" ")
        print "        Now (Local): %s" % submitted_at_local.isoformat(sep=" ")
        print 
        print msg2 
        print

        ctx.exit(CHISUBMIT_FAIL)
    
    if registration.final_submission is not None:
        prior_commit_sha = registration.final_submission.commit_sha
        prior_extensions_used = registration.final_submission.extensions_used             
        prior_submitted_at_utc = registration.final_submission.submitted_at
        prior_submitted_at_local = convert_datetime_to_local(prior_submitted_at_utc)            
        
        submission_commit = conn.get_commit(course, team, prior_commit_sha)            
        
        if prior_commit_sha == commit_sha:
            print "You have already submitted assignment %s" % registration.assignment.assignment_id
            print "You submitted the following commit on %s:" % prior_submitted_at_local
            print
            if submission_commit is None:
                print "WARNING: Previously submitted commit '%s' is not in the repository!" % prior_commit_sha
            else:
                print_commit(submission_commit)
            print
            print "You are trying to submit the same commit again (%s)" % prior_commit_sha
            print "If you want to re-submit, please specify a different commit"
            ctx.exit(CHISUBMIT_FAIL)
            
        if not force:
            print        
            print "You have already submitted assignment %s" % registration.assignment.assignment_id
            print "You submitted the following commit on %s:" % prior_submitted_at_local
            print
            if submission_commit is None:
                print "WARNING: Previously submitted commit '%s' is not in the repository!" % prior_commit_sha
            else:
                print_commit(submission_commit)
            print
            print "If you want to submit again, please use the --force option"
            ctx.exit(CHISUBMIT_FAIL)
        else:
            print
            print "WARNING: You have already submitted assignment %s and you" % registration.assignment.assignment_id 
            print "are about to overwrite the previous submission of the following commit:"
            print
            if submission_commit is None:
                print "WARNING: Previously submitted commit '%s' is not in the repository!" % prior_commit_sha
            else:
                print_commit(submission_commit)
            print

    if registration.final_submission is not None and force:
        msg = "THE ABOVE SUBMISSION FOR %s (%s) WILL BE CANCELLED." % (registration.assignment.assignment_id, registration.assignment.name)
        
        print "!"*len(msg)
        print msg
        print "!"*len(msg)
        print
        print "If you continue, your submission for %s (%s)" % (registration.assignment.assignment_id, registration.assignment.name)
        print "will now point to the following commit:"                
    else:
        print "You are going to make a submission for %s (%s)." % (registration.assignment.assignment_id, registration.assignment.name)
        print "The commit you are submitting is the following:"
    print
    print_commit(commit)
    print
    print "PLEASE VERIFY THIS IS THE EXACT COMMIT YOU WANT TO SUBMIT"
    print
    print "Your team currently has %i extensions" % (submit_response.extensions_before)
    print
    if registration.final_submission is not None:
        print "You used %i extensions in your previous submission of this assignment." % prior_extensions_used
        print "and you are going to use %i additional extensions now." % (extensions - prior_extensions_used)
    else:
        print "You are going to use %i extensions on this submission." % extensions
    print
    print "You will have %i extensions left after this submission." % submit_response.extensions_after
    print 
    print "Are you sure you want to continue? (y/n): ", 
    
    if not yes:
        yesno = raw_input()
    else:
        yesno = 'y'
        print 'y'
    
    if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):
        try:
            submit_response = registration.submit(commit_sha, extensions, dry_run=False)
            
            # TODO: Can't do this until GitLab supports updating tags
            #    
            # message = "Extensions: %i\n" % extensions_requested
            # if submission_tag is None:
            #     conn.create_submission_tag(course, team, tag_name, message, commit.sha)
            # else:
            #     conn.update_submission_tag(course, team, tag_name, message, commit.sha)
            
            print "Your submission has been completed."
            return CHISUBMIT_SUCCESS

        except BadRequestException, bre:        
            print "ERROR: Your submission was not completed. The server reported the following errors:"
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
def student_assignment_cancel_submit(ctx, course, team_id, assignment_id, yes):
    team = get_team_or_exit(ctx, course, team_id)
    registration = get_assignment_registration_or_exit(ctx, team, assignment_id)
    
    if registration.final_submission is None:
        print "Team %s has not made a submission for assignment %s," % (team_id, assignment_id)
        print "so there is nothing to cancel."
        ctx.exit(CHISUBMIT_FAIL)
        
    if is_submission_ready_for_grading(assignment_deadline=registration.assignment.deadline, 
                                       submission_date=registration.final_submission.submitted_at,
                                       extensions_used=registration.final_submission.extensions_used):
        print "You cannot cancel this submission."
        print "You made a submission before the deadline, and the deadline has passed."

        ctx.exit(CHISUBMIT_FAIL)        
            
    conn = create_connection(course, ctx.obj['config'])
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)
        
    submission_commit = conn.get_commit(course, team, registration.final_submission.commit_sha)
        
    print
    print "This is your existing submission for assignment %s:" % assignment_id
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
        
        # TODO: Can't do this until GitLab supports updating tags
        #    
        # message = "Extensions: %i\n" % extensions_requested
        # if submission_tag is None:
        #     conn.create_submission_tag(course, team, tag_name, message, commit.sha)
        # else:
        #     conn.update_submission_tag(course, team, tag_name, message, commit.sha)
            
        print "Your submission has been cancelled."
        

student_assignment.add_command(shared_assignment_list)

student_assignment.add_command(student_assignment_register)
student_assignment.add_command(student_assignment_show_deadline)
student_assignment.add_command(student_assignment_submit)
student_assignment.add_command(student_assignment_cancel_submit)

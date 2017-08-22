import click
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.common.utils import convert_datetime_to_local,\
    create_connection, get_datetime_now_utc, compute_extensions_needed,\
    is_submission_ready_for_grading
from dateutil.parser import parse
from chisubmit.cli.common import pass_course, get_assignment_or_exit,\
    get_team_or_exit, get_assignment_registration_or_exit,\
    catch_chisubmit_exceptions, require_local_config,\
    get_team_registration_from_user
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
        if user.username in partner:
            print "You specified your own username in --partner. You should use this"
            print "option to specify your partners, not including yourself."
            return CHISUBMIT_FAIL
        
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


@click.command(name="cancel-registration")
@click.argument('assignment_id', type=str)
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context  
def student_assignment_cancel_registration(ctx, course, assignment_id, yes):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    # Get registration
    team, registration = get_team_registration_from_user(ctx, course, assignment)
    team_members = team.get_team_members()  
    
    if len(team_members) == 1:
        student = team_members[0].student        
        individual = True
        print "You (%s %s) currently have an INDIVIDUAL registration for %s (%s)" % (student.user.first_name, student.user.last_name, assignment.assignment_id, assignment.name)
    else:
        students = [tm.student for tm in team_members]
        individual = False
        print "You currently have a TEAM registration for %s (%s)." % (assignment.assignment_id, assignment.name)
        print
        print "Team %s has the following students:" % team.team_id
        for s in students:
            print " - %s %s" % (s.user.first_name, s.user.last_name)         
    
    print
    
    if registration.final_submission is not None:
        if individual:
            print "You have already made a submission for %s." % assignment_id
        else:
            print "Team %s has already made a submission for assignment %s." % (team.team_id, assignment_id)
        print
        print "Please cancel your submission first, and then try canceling your registration."
        ctx.exit(CHISUBMIT_FAIL)

    if individual:
        print "Are you sure you want to cancel your registration for this assignment? (y/n): ",
    else:
        print "Are you sure you want to cancel this team's registration for the assignment? (y/n): ",
     
    
    if not yes:
        yesno = raw_input()
    else:
        yesno = 'y'
        print 'y'
    
    if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):        
        try:
            registration.cancel()
            print
            print "Your registration has been cancelled."
            ctx.exit(CHISUBMIT_SUCCESS)
        except BadRequestException, bre:
            response_data = bre.json
            print "ERROR: Your registration cannot be cancelled. The server reported the following:"
            print
            bre.print_errors()

            ctx.exit(CHISUBMIT_FAIL)


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
@click.argument('assignment_id', type=str)
@click.option('--commit-sha', type=str)
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context  
def student_assignment_submit(ctx, course, assignment_id, commit_sha, yes):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    # Determine team for this assignment
    team, registration = get_team_registration_from_user(ctx, course, assignment)
    team_members = team.get_team_members()    
                
    title = "SUBMISSION FOR ASSIGNMENT %s (%s)" % (assignment.assignment_id, assignment.name)
    print title
    print "-" * len(title)
    print
    if len(team_members) == 1:
        student = team_members[0].student
        individual = True
        print "This is an INDIVIDUAL submission for %s %s" % (student.user.first_name, student.user.last_name)
    else:
        students = [tm.student for tm in team_members]
        individual = False
        print "This is a TEAM submission for team %s with the following students:" % team.team_id
        for s in students:
            print " - %s %s" % (s.user.first_name, s.user.last_name)
    print
                
    conn = create_connection(course, ctx.obj['config'])
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)
    
    if commit_sha is None:
        commit = conn.get_latest_commit(course, team)

        if commit is None:
            print "It seems there are no commits in your repository, so I cannot submit anything"
            ctx.exit(CHISUBMIT_FAIL)
                
        user_specified_commit = False
    else:    
        commit = conn.get_commit(course, team, commit_sha)
        
        if commit is None:
            print "Commit %s does not exist in repository" % commit_sha
            ctx.exit(CHISUBMIT_FAIL)

        user_specified_commit = True
        
    try:
        submit_response = registration.submit(commit.sha, dry_run = True)
    except BadRequestException, bre:
        response_data = bre.json
        
        if "extensions_needed" in response_data and "extensions_available" in response_data:
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
            else:
                print "ERROR: Your submission cannot be completed. The server reported the following:"
                print
                bre.print_errors()
        else:
            print "ERROR: Your submission cannot be completed. The server reported the following:"
            print
            bre.print_errors()

        ctx.exit(CHISUBMIT_FAIL)
    
    if registration.final_submission is not None:
        prior_commit_sha = registration.final_submission.commit_sha
        prior_extensions_used = registration.final_submission.extensions_used             
        prior_submitted_at_utc = registration.final_submission.submitted_at
        prior_submitted_at_local = convert_datetime_to_local(prior_submitted_at_utc)            
        
        submission_commit = conn.get_commit(course, team, prior_commit_sha)            
        
        if prior_commit_sha == commit.sha:
            print "You have already submitted assignment %s" % registration.assignment.assignment_id
            print
            print "You submitted the following commit on %s:" % prior_submitted_at_local
            print
            if submission_commit is None:
                print "WARNING: Previously submitted commit '%s' is not in the repository!" % prior_commit_sha
            else:
                print_commit(submission_commit)
            print
            if user_specified_commit:
                print "You are trying to submit the same commit again (%s)" % prior_commit_sha
                print "If you want to re-submit, please specify a different commit."
            else:
                print "The above commit is the latest commit in your repository."
                print
                print "If you were expecting to see a different commit, make sure you've pushed"
                print "your latest code to your repository."
            ctx.exit(CHISUBMIT_FAIL)
            
        print "You have already submitted assignment %s" % registration.assignment.assignment_id
        print
        print "You submitted the following commit on %s:" % prior_submitted_at_local
        print
        if submission_commit is None:
            print "WARNING: Previously submitted commit '%s' is not in the repository!" % prior_commit_sha
        else:
            print_commit(submission_commit)
        print

        msg = "IF YOU CONTINUE, THE ABOVE SUBMISSION FOR %s (%s) WILL BE CANCELLED." % (registration.assignment.assignment_id, registration.assignment.name)
        
        print "!"*len(msg)
        print msg
        print "!"*len(msg)
        print        
        if not user_specified_commit:
            print "If you continue, your submission will instead point to the latest commit in your repository:"
        else:
            print "If you continue, your submission will instead point to the following commit:"                
    else:
        if not user_specified_commit:
            print "The latest commit in your repository is the following:"
        else:
            print "The commit you are submitting is the following:"
    print
    print_commit(commit)
    print
    print "PLEASE VERIFY THIS IS THE EXACT COMMIT YOU WANT TO SUBMIT"
    print
    if individual:
        print "You currently have %i extensions" % (submit_response.extensions_before)
    else:
        print "Your team currently has %i extensions" % (submit_response.extensions_before)
    print
    if registration.final_submission is not None:
        print "You used %i extensions in your previous submission of this assignment." % prior_extensions_used
        print "and you are going to use %i additional extensions now." % (submit_response.extensions_needed - prior_extensions_used)
    else:
        print "You are going to use %i extensions on this submission." % submit_response.extensions_needed
    print
    print "You will have %i extensions left after this submission." % submit_response.extensions_after
    print
    
    if submit_response.in_grace_period:
        print "NOTE: You are submitting after the deadline, but the instructor has"
        print "allowed some extra time after the deadline for students to submit"
        print "without having to consume an extension."
        print
     
    print "Are you sure you want to continue? (y/n): ", 
    
    if not yes:
        yesno = raw_input()
    else:
        yesno = 'y'
        print 'y'
    
    if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):
        try:
            submit_response = registration.submit(commit.sha, dry_run=False)
            
            # TODO: Can't do this until GitLab supports updating tags
            #    
            # message = "Extensions: %i\n" % extensions_requested
            # if submission_tag is None:
            #     conn.create_submission_tag(course, team, tag_name, message, commit.sha)
            # else:
            #     conn.update_submission_tag(course, team, tag_name, message, commit.sha)
            
            print
            print "Your submission has been completed."

            if submit_response.in_grace_period:
                print
                print "Your submission was made during the deadline's grace period. This means"
                print "that, although your submission was technically made *after* the"
                print "deadline, we are counting it as if it had been made before the deadline."
                print
                print "In the future, you should not rely on the presence of this grace period!"
                print "Your instructor may choose not to use one in future assignments, or may"
                print "use a shorter grace period. Your instructor is also aware of what"
                print "submissions are made during the grace period; if you repeatedly submit"
                print "during the grace period, your instructor may charge you an extension"
                print "or refuse to accept your assignment if you are out of extensions."
            
            return CHISUBMIT_SUCCESS

        except BadRequestException, bre:
            print        
            print "ERROR: Your submission was not completed. The server reported the following errors:"
            bre.print_errors()
            return CHISUBMIT_FAIL
    else:
        print "Your submission has not been completed."
        print
        print "If you chose not to proceed because the above commit is not the one you wanted"
        print "to submit, make sure you've pushed your latest code to your repository before"
        print "attempting to submit again."
        print
        print "If you want to submit a different commit from your latest commit (e.g., an earlier"
        print "commit), you can use the --commit-sha option to specify a different commit."
        return CHISUBMIT_FAIL
    
    
@click.command(name="cancel-submit")   
@click.argument('assignment_id', type=str)
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context  
def student_assignment_cancel_submit(ctx, course, assignment_id, yes):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    # Determine team for this assignment
    team, registration = get_team_registration_from_user(ctx, course, assignment)
    team_members = team.get_team_members()    
    
    if len(team_members) == 1:
        individual = True
    else:
        individual = False    
    
    if registration.final_submission is None:
        if individual:
            print "You have not made a submission for assignment %s," % assignment_id
        else:
            print "Team %s has not made a submission for assignment %s," % (team.team_id, assignment_id)
        print "so there is nothing to cancel."
        ctx.exit(CHISUBMIT_FAIL)
        
    if registration.grading_started:
        print "You cannot cancel this submission."
        print "You made a submission and it has already been sent to the graders for grading."
        print "Please contact an instructor if you wish to amend your submission."

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
        print
        print "Your submission has been cancelled."
        

student_assignment.add_command(shared_assignment_list)

student_assignment.add_command(student_assignment_register)
student_assignment.add_command(student_assignment_cancel_registration)
student_assignment.add_command(student_assignment_show_deadline)
student_assignment.add_command(student_assignment_submit)
student_assignment.add_command(student_assignment_cancel_submit)

import click
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.common.utils import convert_datetime_to_local,\
    create_connection, get_datetime_now_utc, compute_extensions_needed
from dateutil.parser import parse
from chisubmit.cli.common import pass_course
from chisubmit.cli.shared.assignment import shared_assignment_list
from datetime import timedelta


@click.group(name="assignment")
@click.pass_context
def student_assignment(ctx):
    pass


@click.command(name="register")
@click.argument('assignment_id', type=str)
@click.option('--team-name', type=str)
@click.option('--partner', type=str, multiple=True)
@pass_course
@click.pass_context
def student_assignment_register(ctx, course, assignment_id, team_name, partner):
    a = Assignment.from_id(course.id, assignment_id)
        
    a.register(team_name = team_name,
               partners = partner)
    
    return CHISUBMIT_SUCCESS

@click.command(name="show-deadline")
@click.argument('assignment_id', type=str)
@click.option('--utc', is_flag=True)
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
@pass_course
@click.pass_context  
def student_assignment_submit(ctx, course, team_id, assignment_id, commit_sha, extensions, force, yes):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)
    
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)
    
    ta = team.get_assignment(assignment_id)
    if ta is None:
        print "Team %s is not registered for assignment %s" % (team_id, assignment_id)
        ctx.exit(CHISUBMIT_FAIL)
        
    if team.has_assignment_ready_for_grading(assignment):
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

    response = assignment.submit(team_id, commit_sha, extensions, dry_run=True)

    success = response["success"]
    dry_run = response["dry_run"]

    deadline_utc = parse(response["submission"]["deadline"])
    
    submitted_at_utc = parse(response["submission"]["submitted_at"])
    extensions_needed = response["submission"]["extensions_needed"]
    extensions_requested = response["submission"]["extensions_requested"]    

    extensions_available_before = response["team"]["extensions_available_before"]
    extensions_available = response["team"]["extensions_available"]

    if response["prior_submission"]["submitted_at"] is not None:    
        prior_submitted_at_utc = parse(response["prior_submission"]["submitted_at"])
        prior_submitted_at_local = convert_datetime_to_local(prior_submitted_at_utc)
    prior_commit_sha = response["prior_submission"]["commit_sha"]
    prior_extensions_used = response["prior_submission"]["extensions_used"]

    deadline_local = convert_datetime_to_local(deadline_utc)
    submitted_at_local = convert_datetime_to_local(submitted_at_utc)
        
    if not success:
        if extensions_needed > extensions_available:
            msg1 = "You do not have enough extensions to submit this assignment."
            msg2 = "You would need %i extensions to submit this assignment at this " \
                   "time, but you only have %i left" % (extensions_needed, extensions_available)
        elif extensions_requested < extensions_needed:
            msg1 = "The number of extensions you have requested is insufficient."
            msg2 = "You need to request %s extensions." % extensions_needed
        elif extensions_requested > extensions_needed:
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
    else:             
        if prior_commit_sha is not None:
            submission_commit = conn.get_commit(course, team, prior_commit_sha)
            
            if prior_commit_sha == commit_sha:
                print "You have already submitted assignment %s" % assignment.id
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
                print "You have already submitted assignment %s" % assignment.id
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
                print "WARNING: You have already submitted assignment %s and you" % assignment.id 
                print "are about to overwrite the previous submission of the following commit:"
                print
                if submission_commit is None:
                    print "WARNING: Previously submitted commit '%s' is not in the repository!" % prior_commit_sha
                else:
                    print_commit(submission_commit)
                print
    
        if prior_commit_sha is not None and force:
            msg = "THE ABOVE SUBMISSION FOR %s (%s) WILL BE CANCELLED." % (assignment.id, assignment.name)
            
            print "!"*len(msg)
            print msg
            print "!"*len(msg)
            print
            print "If you continue, your submission for %s (%s)" % (assignment.id, assignment.name)
            print "will now point to the following commit:"                
        else:
            print "You are going to make a submission for %s (%s)." % (assignment.id, assignment.name)
            print "The commit you are submitting is the following:"
        print
        print_commit(commit)
        print
        print "PLEASE VERIFY THIS IS THE EXACT COMMIT YOU WANT TO SUBMIT"
        print
        print "Your team currently has %i extensions" % (extensions_available_before)
        print
        if prior_commit_sha is not None:
            print "You used %i extensions in your previous submission of this assignment." % prior_extensions_used
            print "and you are going to use %i additional extensions now." % (extensions_needed - prior_extensions_used)
        else:
            print "You are going to use %i extensions on this submission." % extensions_needed
        print
        print "You will have %i extensions left after this submission." % extensions_available
        print 
        print "Are you sure you want to continue? (y/n): ", 
        
        if not yes:
            yesno = raw_input()
        else:
            yesno = 'y'
            print 'y'
        
        if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):
            response = assignment.submit(team_id, commit_sha, extensions, dry_run=False)
              
            # TODO: Can't do this until GitLab supports updating tags
            #    
            # message = "Extensions: %i\n" % extensions_requested
            # if submission_tag is None:
            #     conn.create_submission_tag(course, team, tag_name, message, commit.sha)
            # else:
            #     conn.update_submission_tag(course, team, tag_name, message, commit.sha)
                
            print
            if response["success"]:
                print "Your submission has been completed."
            else:
                print "ERROR: Your submission was not completed."
            
        return CHISUBMIT_SUCCESS
    
    
@click.command(name="cancel-submit")
@click.argument('team_id', type=str)    
@click.argument('assignment_id', type=str)
@click.option('--yes', is_flag=True)
@pass_course
@click.pass_context  
def student_assignment_cancel_submit(ctx, course, team_id, assignment_id, yes):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)
    
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)
        
    ta = team.get_assignment(assignment_id)
    if ta is None:
        print "Team %s is not registered for assignment %s" % (team_id, assignment_id)
        ctx.exit(CHISUBMIT_FAIL)
        
    if ta.submitted_at is None:
        print "Team %s has not made a submission for assignment %s," % (team_id, assignment_id)
        print "so there is nothing to cancel."
        ctx.exit(CHISUBMIT_FAIL)
        
    if ta.submitted_at is not None:
        now = get_datetime_now_utc()
        deadline = assignment.deadline + timedelta(days=ta.extensions_used)
        
        if now > deadline:
            print "You cannot cancel this submission."
            print "You made a submission before the deadline, and the deadline has passed."

            ctx.exit(CHISUBMIT_FAIL)        
            
    conn = create_connection(course, ctx.obj['config'])
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)
        
    submission_commit = conn.get_commit(course, team, ta.commit_sha)
        
    print
    print "This is your existing submission for assignment %s:" % assignment.id 
    print
    if submission_commit is None:
        print "WARNING: Previously submitted commit '%s' is not in the repository!" % ta.commit_sha
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
        response = assignment.cancel(team_id)
        
        # TODO: Can't do this until GitLab supports updating tags
        #    
        # message = "Extensions: %i\n" % extensions_requested
        # if submission_tag is None:
        #     conn.create_submission_tag(course, team, tag_name, message, commit.sha)
        # else:
        #     conn.update_submission_tag(course, team, tag_name, message, commit.sha)
            
        print
        if response["success"]:
            print "Your submission has been cancelled."
        else:
            print "ERROR: Your submission was not cancelled."
        

student_assignment.add_command(shared_assignment_list)

student_assignment.add_command(student_assignment_register)
student_assignment.add_command(student_assignment_show_deadline)
student_assignment.add_command(student_assignment_submit)
student_assignment.add_command(student_assignment_cancel_submit)

import click
from chisubmit.cli.common import pass_course, get_team_or_exit,\
    get_assignment_or_exit, catch_chisubmit_exceptions, require_local_config
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS,\
    ChisubmitException
import operator
from chisubmit.common.utils import convert_datetime_to_local

@click.command(name="list")
@click.option('--ids', is_flag=True)
@click.option('--assignment', type=str)
@click.option('--include-inactive', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def shared_team_list(ctx, course, ids, assignment, include_inactive):
    teams = course.get_teams()
    teams.sort(key=operator.attrgetter("team_id"))

    assignment_id = assignment
    if assignment_id is not None:
        assignment = get_assignment_or_exit(ctx, course, assignment_id)
    else:
        assignment = None

    for team in teams:
        registrations = team.get_assignment_registrations()
        
        if assignment is not None:
            if not assignment.assignment_id in [r.assignment.assignment_id for r in registrations]:
                continue
            
        if not (team.active or include_inactive):
            continue
        
        if ids:
            print team.team_id
        else:
            team_members = team.get_team_members()
            
            if len(team_members) == 0:
                students = "No students"
            else:
                students = "Students: " + ",".join([tm.student.user.username for tm in team_members])
            if len(registrations) == 0:
                assignments = "No assignments"
            else:
                assignments = "Assignments: " + ",".join([r.assignment.assignment_id for r in registrations])
            fields = [team.team_id, students, assignments]

            print "  ".join(fields)

    return CHISUBMIT_SUCCESS

@click.command(name="show")
@click.argument('team_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def shared_team_show(ctx, course, team_id):
    team = get_team_or_exit(ctx, course, team_id)
        
    print "Team name: %s" % team.team_id
    print
    if course.extension_policy == "per-team":
        print "Extensions available: %i" % team.extensions 
        print
    
    team_members = team.get_team_members()
    
    if len(team_members) == 0:
        print "No students in this team"
    else:
        print "STUDENTS"
        print "--------"
        for team_member in team_members:
            if team_member.confirmed:
                status = "CONFIRMED"
            else:
                status = "UNCONFIRMED"

            user = team_member.student.user

            print "%s: %s, %s  (%s)" % (user.username, user.last_name, user.first_name, status)

    print

    registrations = team.get_assignment_registrations()

    if len(registrations) == 0:
        print "This team is not registered for any assignments."
    else:
        print "ASSIGNMENTS"
        print "-----------"
        for r in registrations:
            assignment = r.assignment
            print "ID: %s" % assignment.assignment_id
            print "Name: %s" % assignment.name
            print "Deadline: %s" % convert_datetime_to_local(assignment.deadline).isoformat(" ")        
            if r.final_submission is not None:
                print "Last submitted at: %s" % convert_datetime_to_local(r.final_submission.submitted_at).isoformat(" ")
                print "Commit SHA: %s" % r.final_submission.commit_sha
                print "Extensions used: %i" % r.final_submission.extensions_used
            else:
                print "NOT SUBMITTED"    
            print    

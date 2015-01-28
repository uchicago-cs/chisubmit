import click
from chisubmit.cli.common import pass_course
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS,\
    ChisubmitException
import operator
from chisubmit.common.utils import convert_datetime_to_local

@click.command(name="list")
@click.option('--ids', is_flag=True)
@click.option('--assignment', type=str)
@click.option('--include-inactive', is_flag=True)
@pass_course
@click.pass_context
def shared_team_list(ctx, course, ids, assignment, include_inactive):
    teams = course.get_teams()
    teams.sort(key=operator.attrgetter("id"))

    assignment_id = assignment
    assignment = None
    if assignment_id is not None:
        assignment = course.get_assignment(assignment_id)
        if assignment is None:
            print "Assignment %s does not exist" % assignment_id
            ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        if assignment is not None:
            if not team.has_assignment(assignment.id):
                continue
            
        if not (team.active or include_inactive):
            continue
        
        if ids:
            print team.id
        else:
            if len(team.students) == 0:
                students = "No students"
            else:
                students = "Students: " + ",".join([s.user.id for s in team.students])
            if len(team.assignments) == 0:
                assignments = "No assignments"
            else:
                assignments = "Assignments: " + ",".join([a.assignment_id for a in team.assignments])
            fields = [team.id, students, assignments]

            print "  ".join(fields)

    return CHISUBMIT_SUCCESS

@click.command(name="show")
@click.argument('team_id', type=str)
@pass_course
@click.pass_context
def shared_team_show(ctx, course, team_id):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)
        
    print "Team name: %s" % team.id
    print
    print "Extensions available: %i" % team.extensions_available 
    print
    
    if len(team.extras) > 0:
        print "Attributes:"
        for k,v in team.extras.items():
            print " - %s: %s" % (k,v)
        print
    
    if len(team.students) == 0:
        print "No students in this team"
    else:
        print "STUDENTS"
        print "--------"
        for student in team.students:
            if student.status == 0:
                status = "UNCONFIRMED"
            elif student.status == 1:
                status = "CONFIRMED"
            else:
                raise ChisubmitException("Student '%s' in team '%s' has unknown status %i" % (student.user.id, team.id, student.status))
            print "%s: %s, %s  (%s)" % (student.user.id, student.user.last_name, student.user.first_name, status)

    print

    if len(team.assignments) == 0:
        print "This team is not registered for any assignments."
    else:
        print "ASSIGNMENTS"
        print "-----------"
        for ta in team.assignments:
            assignment = course.get_assignment(ta.assignment_id)
            print "ID: %s" % assignment.id
            print "Name: %s" % assignment.name
            print "Deadline: %s" % convert_datetime_to_local(assignment.deadline).isoformat(" ")        
            if ta.submitted_at is not None:
                print "Last submitted at: %s" % convert_datetime_to_local(ta.submitted_at).isoformat(" ")
                print "Commit SHA: %s" % ta.commit_sha
                print "Extensions used: %i" % ta.extensions_used
            else:
                print "NOT SUBMITTED"    
            print    

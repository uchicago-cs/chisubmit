import click
from chisubmit.cli.common import pass_course, DATETIME, get_assignment_or_exit,\
    catch_chisubmit_exceptions, require_local_config
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.common.utils import convert_datetime_to_utc
import operator
from chisubmit.cli.shared.assignment import shared_assignment_list,\
    shared_assignment_set_attribute
from chisubmit.client.exceptions import UnknownObjectException


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
    unsubmitted = []
    
    for team in course.get_teams():
        try:
            registration = team.get_assignment_registration(assignment.assignment_id)
        except UnknownObjectException:
            continue
        
        nteams += 1
        
        if registration.final_submission is not None:
            nsubmissions += 1
        else:
            unsubmitted.append(team)
            
        unconfirmed = False
        for tm in team.get_team_members():
            if tm.username not in dropped:
                try:
                    students.remove(tm.username)
                    nstudents_assignment += 1
                    if not tm.confirmed:
                        unconfirmed = True
                except KeyError, ke:
                    print "WARNING: Student %s seems to be in more than one team (offending team: %s)" % (tm.username, team.team_id)
            
        if unconfirmed:
            teams_unconfirmed.append(team)
                
    assert(nstudents == len(students) + nstudents_assignment)                
            
    title = "Assignment '%s'" % (assignment.name)
    print title
    print "=" * len(title)
               
    print 
    print "%i / %i students in %i teams have signed up for assignment %s" % (nstudents_assignment, nstudents, nteams, assignment.assignment_id)
    print
    print "%i / %i teams have submitted the assignment" % (nsubmissions, nteams)
    
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
instructor_assignment.add_command(instructor_assignment_stats)


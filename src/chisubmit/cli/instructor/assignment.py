import click
from chisubmit.cli.common import pass_course, DATETIME
from chisubmit.client.assignment import Assignment, GradeComponent
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from dateutil.parser import parse
from chisubmit.common.utils import convert_datetime_to_utc,\
    convert_datetime_to_local
import operator
from chisubmit.cli.shared.course import shared_course_list
from chisubmit.cli.shared.assignment import shared_assignment_list


@click.group(name="assignment")
@click.pass_context
def instructor_assignment(ctx):
    pass


@click.command(name="add")
@click.argument('assignment_id', type=str)
@click.argument('name', type=str)
@click.argument('deadline', type=DATETIME)
@pass_course
@click.pass_context
def instructor_assignment_add(ctx, course, assignment_id, name, deadline):
    deadline = convert_datetime_to_utc(deadline)
    
    assignment = Assignment(id = assignment_id,
                            name = name,
                            deadline = deadline,
                            course_id = course.id)
    
    return CHISUBMIT_SUCCESS






@click.command(name="add-grade-component")
@click.argument('assignment_id', type=str)
@click.argument('grade_component_id', type=str)
@click.argument('description', type=str)
@click.argument('points', type=float)
@pass_course
@click.pass_context
def instructor_assignment_add_grade_component(ctx, course, assignment_id, grade_component_id, description, points):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    grade_component = GradeComponent(id = grade_component_id, description = description, points=points)
    assignment.add_grade_component(grade_component)

    return CHISUBMIT_SUCCESS


@click.command(name="stats")
@click.argument('assignment_id', type=str)
@pass_course
@click.pass_context
def instructor_assignment_stats(ctx, course, assignment_id):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)
        
    title = "Assignment '%s'" % (assignment.name)
    print title
    print "=" * len(title)
         
    student_dict = {s.user.id: s.user for s in course.students if not s.dropped}
    students = set(student_dict.keys())
    dropped = set([s.user.id for s in course.students if s.dropped])
    
    teams_unconfirmed = []
    nteams = 0
    nstudents = len(student_dict)
    nstudents_assignment = 0
    nsubmissions = 0
    
    for team in course.teams:
        if team.has_assignment(assignment.id):
            nteams += 1
            
            if team.has_submitted(assignment.id):
                nsubmissions += 1
            
            unconfirmed = False
            for student in team.students:
                student_id = student.user.id
                if student_id not in dropped:
                    try:
                        students.remove(student_id)
                        nstudents_assignment += 1
                        if student.status == 0: # Unconfirmed
                            unconfirmed = True
                    except KeyError, ke:
                        print "WARNING: Student %s seems to be in more than one team (offending team: %s)" % (student_id, team.id)
                
            if unconfirmed:
                teams_unconfirmed.append(team)
                
    assert(nstudents == len(students) + nstudents_assignment)                
               
    print 
    print "%i / %i students in %i teams have signed up for assignment %s" % (nstudents_assignment, nstudents, nteams, assignment.id)
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
    
    return CHISUBMIT_SUCCESS


instructor_assignment.add_command(shared_assignment_list)

instructor_assignment.add_command(instructor_assignment_add)
instructor_assignment.add_command(instructor_assignment_add_grade_component)

instructor_assignment.add_command(instructor_assignment_stats)


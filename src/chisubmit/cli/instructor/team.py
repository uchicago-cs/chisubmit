import click
from chisubmit.cli.common import pass_course, DATETIME
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory

import pprint
import operator

@click.group(name="team")
@click.pass_context
def instructor_team(ctx):
    pass

@click.command(name="list")
@click.option('--ids', is_flag=True)
@pass_course
@click.pass_context
def instructor_team_list(ctx, course, ids):
    teams = course.teams[:]
    teams.sort(key=operator.attrgetter("id"))

    for team in teams:
        if ids:
            print team.id
        else:
            fields = [team.id, `team.active`]

            print "\t".join(fields)

    return CHISUBMIT_SUCCESS


@click.command(name="show")
@click.option('--search', is_flag=True)
@click.option('--verbose', is_flag=True)
@click.argument('team_id', type=str)
@pass_course
@click.pass_context
def instructor_team_show(ctx, course, search, verbose, team_id):
    if not search:
        team = course.get_team(team_id)
        if team is None:
            print "Team %s does not exist" % team_id
            ctx.exit(CHISUBMIT_FAIL)

        teams = [team]
    else:
        teams = course.search_team(team_id)

    pp = pprint.PrettyPrinter(indent=4, depth=6)

    for t in teams:
        tdict = dict(vars(t))
        if verbose:
            tdict["assignments"] = dict(tdict["assignments"])
            for p in tdict["assignments"]:
                tdict["assignments"][p] = vars(tdict["assignments"][p])

            tdict["students"] = [vars(s) for s in tdict["students"]]

        pp.pprint(tdict)

    return CHISUBMIT_SUCCESS


@click.command(name="student-add")
@click.argument('team_id', type=str)
@click.argument('student_id', type=str)
@pass_course
@click.pass_context
def instructor_team_student_add(ctx, course, team_id, student_id):
    student = course.get_student(student_id)
    if student is None:
        print "Student %s does not exist" % student_id
        ctx.exit(CHISUBMIT_FAIL)

    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

    team.add_student(student)

    return CHISUBMIT_SUCCESS


@click.command(name="assignment-add")
@click.argument('team_id', type=str)
@click.argument('assignment_id', type=str)
@pass_course
@click.pass_context
def instructor_team_assignment_add(ctx, course, team_id, assignment_id):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

    if team.assignments.has_key(assignment.id):
        print "Team %s has already been assigned assignment %s"  % (team.id, assignment.id)
        ctx.exit(CHISUBMIT_FAIL)

    team.add_assignment(assignment)

    return CHISUBMIT_SUCCESS


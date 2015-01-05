import click

from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
import operator
import random
from chisubmit.repos.grading import GradingGitRepo
import os.path
from chisubmit.rubric import RubricFile
from chisubmit.cli.common import create_grading_repos, get_teams,\
    gradingrepo_push_grading_branch, gradingrepo_pull_grading_branch
from chisubmit.cli.common import pass_course
from chisubmit.common.utils import create_connection

@click.group(name="grading")
@click.pass_context
def instructor_grading(ctx):
    pass


@click.command(name="set-grade")
@click.argument('team_id', type=str)
@click.argument('assignment_id', type=str)
@click.argument('grade_component_id', type=str)
@click.argument('points', type=float)
@pass_course
@click.pass_context
def instructor_grading_set_grade(ctx, course, team_id, assignment_id, grade_component_id, points):   
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

    grade_component = assignment.get_grade_component(grade_component_id)
    if not grade_component:
        print "Assignment %s does not have a grade component '%s'" % (assignment.id, grade_component)
        ctx.exit(CHISUBMIT_FAIL)
    
    team.set_assignment_grade(assignment_id, grade_component.id, points)


@click.command(name="add-conflict")
@click.argument('grader_id', type=str)
@click.argument('student_id', type=str)
@pass_course
@click.pass_context
def instructor_grading_add_conflict(ctx, course, grader_id, student_id):
    grader = course.get_grader(grader_id)
    if not grader:
        print "Grader %s does not exist" % grader_id
        ctx.exit(CHISUBMIT_FAIL)

    student = course.get_student(student_id)
    if not student:
        print "Student %s does not exist" % student_id
        ctx.exit(CHISUBMIT_FAIL)

    if student in grader.conflicts:
        print "Student %s is already listed as a conflict for grader %s" % (student.id, grader.id)

    grader.conflicts.append(student)

    return CHISUBMIT_SUCCESS

@click.command(name="list-grades")
@pass_course
@click.pass_context
def instructor_grading_list_grades(ctx, course):
    students = [s for s in course.students if not s.dropped]
    assignments = course.assignments

    students.sort(key=operator.attrgetter("user.last_name"))
    assignments.sort(key=operator.attrgetter("deadline"))

    student_grades = dict([(s.user.id,dict([(a.id,{}) for a in assignments])) for s in students])

    for team in course.teams:
        for team_assignment in team.assignments:
            assignment_id = team_assignment.assignment_id
            for student in team.students:
                student_id = student.user.id
                if student_grades.has_key(student_id):
                    g = student_grades[student_id][assignment_id]
                    for grade in team_assignment.grades:
                        gc_id = grade.grade_component_id
                        if g.has_key(gc_id):
                            print "Warning: %s already has a grade for grade component %i" % (student_id, gc_id)
                        else:
                            g[gc_id] = grade.points
                    g["__PENALTIES"] = team_assignment.get_total_penalties()
                    g["__TOTAL"] = team_assignment.get_total_grade()

    fields = ["Last Name","First Name"]
    for assignment in assignments:
        fields += ["%s - %s" % (assignment.id, gc.description) for gc in assignment.grade_components]
        fields.append("%s - Penalties" % assignment.id)
        fields.append("%s - Total" % assignment.id)

    print ",".join(fields)

    for student in students:
        fields = [student.user.last_name, student.user.first_name]
        for assignment in assignments:
            for gc in assignment.grade_components:
                grades = student_grades[student.user.id][assignment.id]
                if not grades.has_key(gc.id):
                    fields.append("")
                else:
                    fields.append(str(grades[gc.id]))
            if len(grades) == 0:
                fields += ["",""]
            else:
                fields.append(str(grades["__PENALTIES"]))
                fields.append(str(grades["__TOTAL"]))

        print ",".join(fields)


@click.command(name="assign-graders")
@click.argument('assignment_id', type=str)
@click.option('--from-assignment', type=str)
@click.option('--avoid-assignment', type=str)
@click.option('--reset', is_flag=True)
@pass_course
@click.pass_context
def instructor_grading_assign_graders(ctx, course, assignment_id, from_assignment, avoid_assignment, reset):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    from_assignment = None
    if from_assignment is not None:
        from_assignment = course.get_assignment(from_assignment)
        if from_assignment is None:
            print "Project %s does not exist" % from_assignment
            ctx.exit(CHISUBMIT_FAIL)

    avoid_assignment = None
    if avoid_assignment is not None:
        avoid_assignment = course.get_assignment(avoid_assignment)
        if avoid_assignment is None:
            print "Project %s does not exist" % avoid_assignment
            ctx.exit(CHISUBMIT_FAIL)

    if reset and from_assignment is not None:
        print "--reset and --from_assignment are mutually exclusive"
        ctx.exit(CHISUBMIT_FAIL)

    if avoid_assignment is not None and from_assignment is not None:
        print "--avoid_assignment and --from_assignment are mutually exclusive"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment)
    graders = course.graders[:]

    if len(graders) == 0:
        print "There are ZERO graders in this course!"
        ctx.exit(CHISUBMIT_FAIL)

    min_teams_per_grader = len(teams) / len(graders)
    extra_teams = len(teams) % len(graders)

    teams_per_grader = dict([(g.user.id, min_teams_per_grader) for g in graders])
    random.shuffle(graders)

    # so many graders in this course that some will end up expecting zero
    # teams to grade. Make sure they are able to get at least one.
    for g in graders[:extra_teams]:
        teams_per_grader[g.user.id] += 1

    if from_assignment is not None:
        common_teams = [t for t in course.teams if t.has_assignment(assignment.id) and t.has_assignment(from_assignment.id)]
        for t in common_teams:
            team_assignment_from = t.get_assignment(from_assignment.id)
            team_assignment_to = t.get_assignment(assignment.id)

            # try to assign the same grader that would grade the same team's other assignment
            grader = team_assignment_from.grader
            if grader is not None and teams_per_grader[grader.id] > 0:
                team_assignment_to.grader = grader
                teams_per_grader[grader.id] -= 1

    if reset:
        for t in teams:
            t.get_assignment(assignment.id).grader = None

    for g in graders:
        if teams_per_grader[g.user.id] > 0:
            for t in teams:
                team_assignment = t.get_assignment(assignment.id)

                if avoid_assignment is not None:
                    team_assignment_avoid = t.get_assignment(avoid_assignment.id)
                    if team_assignment_avoid.grader == grader:
                        continue
                
                team_assignment_grader = team_assignment.grader
                if team_assignment_grader is None:
                    valid = True

                    for s in t.students:
                        conflicts = g.get_conflicts()
                        if s.user.id in conflicts:
                            valid = False
                            break

                    if valid:
                        t.set_assignment_grader(assignment.id, g.user.id)
                        teams_per_grader[g.user.id] -= 1
                        if teams_per_grader[g.user.id] == 0:
                            break

    for g in graders:
        if teams_per_grader[g.user.id] != 0:
            print "Unable to assign enough teams to grader %s" % g.user.id

    for t in teams:
        team_assignment = t.get_assignment(assignment.id)
        if team_assignment.grader is None:
            print "Team %s has no grader" % (t.id)

    return CHISUBMIT_SUCCESS


@click.command(name="list-grader-assignments")
@click.argument('assignment_id', type=str)
@click.option('--grader-id', type=str)
@pass_course
@click.pass_context
def instructor_grading_list_grader_assignments(ctx, course, assignment_id, grader_id):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    if grader_id is not None:
        grader = course.get_grader(grader_id)
        if grader is None:
            print "Grader %s does not exist" % grader_id
            ctx.exit(CHISUBMIT_FAIL)
    else:
        grader = None

    teams = get_teams(course, assignment)
    teams.sort(key=operator.attrgetter("id"))

    for t in teams:
        team_assignment = t.get_assignment(assignment.id)
        if grader is None:
            if team_assignment.grader is None:
                grader_str = "<no-grader-assigned>"
            else:
                grader_str = team_assignment.grader.id
            print t.id, grader_str
        else:
            if grader == team_assignment.grader:
                print t.id

    return CHISUBMIT_SUCCESS


@click.command(name="list-submissions")
@click.argument('assignment_id', type=str)
@pass_course
@click.pass_context
def instructor_grading_list_submissions(ctx, course, assignment_id):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment)
    teams.sort(key=operator.attrgetter("id"))

    conn = create_connection(course, ctx.obj['config'])

    for team in teams:
        submission_tag = conn.get_submission_tag(course, team, assignment.id)

        if submission_tag is None:
            print "%25s NOT SUBMITTED" % team.id
        else:
            print "%25s SUBMITTED" % team.id

    return CHISUBMIT_SUCCESS

@click.command(name="create-grading-repos")
@click.argument('assignment_id', type=str)
@pass_course
@click.pass_context
def instructor_grading_create_grading_repos(ctx, course, assignment_id):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment)

    repos = create_grading_repos(ctx.obj['config'], course, assignment, teams)

    if repos == None:
        ctx.exit(CHISUBMIT_FAIL)

    return CHISUBMIT_SUCCESS


@click.command(name="create-grading-branches")
@click.argument('assignment_id', type=str)
@click.option('--only', type=str)
@pass_course
@click.pass_context
def instructor_grading_create_grading_branches(ctx, course, assignment_id, only):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, only = only)

    if teams is None:
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, assignment)

        if repo is None:
            print "%s does not have a grading repository" % team.id
            continue

        repo.create_grading_branch()
        print "Created grading branch for %s" % team.id

    return CHISUBMIT_SUCCESS


@click.command(name="push-grading-branches")
@click.argument('assignment_id', type=str)
@click.option('--to-staging', is_flag=True)
@click.option('--to-students', is_flag=True)
@click.option('--only', type=str)
@pass_course
@click.pass_context
def instructor_grading_push_grading_branches(ctx, course, assignment_id, to_staging, to_students, only):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, only = only)

    if teams is None:
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        print ("Pushing grading branch for team %s... " % team.id),
        gradingrepo_push_grading_branch(ctx.obj['config'], course, team, assignment, to_staging = to_staging, to_students = to_students)
        print "done."

    return CHISUBMIT_SUCCESS



@click.command(name="pull-grading-branches")
@click.argument('assignment_id', type=str)
@click.option('--from-staging', is_flag=True)
@click.option('--from-students', is_flag=True)
@click.option('--only', type=str)
@pass_course
@click.pass_context
def instructor_grading_pull_grading_branches(ctx, course, assignment_id, from_staging, from_students, only):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, only = only)

    if teams is None:
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        print "Pulling grading branch for team %s... " % team.id
        gradingrepo_pull_grading_branch(ctx.obj['config'], course, team, assignment, from_staging = from_staging, from_students = from_students)

    return CHISUBMIT_SUCCESS



@click.command(name="add-rubrics")
@click.argument('assignment_id', type=str)
@pass_course
@click.pass_context
def instructor_grading_add_rubrics(ctx, course, assignment_id):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment)

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, assignment)
        team_assignment = team.get_assignment(assignment_id)
        rubric = RubricFile.from_assignment(assignment, team_assignment)
        rubricfile = repo.repo_path + "/%s.rubric.txt" % assignment.id
        print rubricfile
        rubric.save(rubricfile, include_blank_comments=True)


@click.command(name="collect-rubrics")
@click.argument('assignment_id', type=str)
@pass_course
@click.pass_context
def instructor_grading_collect_rubrics(ctx, course, assignment_id):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    gcs = assignment.grade_components

    teams = get_teams(course, assignment)

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, assignment)
        if repo is None:
            print "Repository for %s does not exist" % (team.id)
            ctx.exit(CHISUBMIT_FAIL)

        rubricfile = repo.repo_path + "/%s.rubric.txt" % assignment.id

        if not os.path.exists(rubricfile):
            print "Repository for %s does not have a rubric for assignment %s" % (team.id, assignment.id)
            ctx.exit(CHISUBMIT_FAIL)

        rubric = RubricFile.from_file(open(rubricfile), assignment)

        points = []
        for gc in gcs:
            grade = rubric.points[gc.description]
            if grade is None:
                team.set_assignment_grade(assignment.id, gc.id, 0)
                points.append("")
            else:
                team.set_assignment_grade(assignment.id, gc.id, grade)
                points.append(`grade`)

        penalties = {}
        if rubric.penalties is not None:
            for desc, p in rubric.penalties.items():
                penalties[desc] = p

        team.set_assignment_penalties(assignment.id, penalties)

        new_team = course.get_team(team.id)
        assignment_team = new_team.get_assignment(assignment.id)

        print "%s: %s" % (new_team.id, assignment_team.get_total_grade())

instructor_grading.add_command(instructor_grading_set_grade)
instructor_grading.add_command(instructor_grading_list_grades)
instructor_grading.add_command(instructor_grading_assign_graders)
instructor_grading.add_command(instructor_grading_list_grader_assignments)
instructor_grading.add_command(instructor_grading_list_submissions)
instructor_grading.add_command(instructor_grading_create_grading_repos)
instructor_grading.add_command(instructor_grading_create_grading_branches)
instructor_grading.add_command(instructor_grading_push_grading_branches)
instructor_grading.add_command(instructor_grading_pull_grading_branches)
instructor_grading.add_command(instructor_grading_add_rubrics)
instructor_grading.add_command(instructor_grading_collect_rubrics)

import click

from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.repos.grading import GradingGitRepo
from chisubmit.rubric import RubricFile, ChisubmitRubricException
from chisubmit.cli.common import create_grading_repos, get_teams,\
    gradingrepo_push_grading_branch, gradingrepo_pull_grading_branch
from chisubmit.cli.common import pass_course
from chisubmit.common.utils import create_connection

import csv
import operator
import random
import itertools
import os.path
from pprint import pprint

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
        
    ta = team.get_assignment(assignment_id)
    if ta is None:
        print "Team %s is not registered for assignment %s" % (team_id, assignment_id)
        ctx.exit(CHISUBMIT_FAIL)

    grade_component = assignment.get_grade_component(grade_component_id)
    if not grade_component:
        print "Assignment %s does not have a grade component '%s'" % (assignment.id, grade_component)
        ctx.exit(CHISUBMIT_FAIL)
        
    if points < 0 or points > grade_component.points:
        print "Invalid grade value %.2f (%s must be 0 <= x <= %.2f)" % (points, grade_component_id, grade_component.points)
        ctx.exit(CHISUBMIT_FAIL)
    
    team.set_assignment_grade(assignment_id, grade_component.id, points)


@click.command(name="load-grades")
@click.argument('assignment_id', type=str)
@click.argument('grade_component_id', type=str)
@click.argument('csv_file', type=click.File('rb'))
@click.argument('csv_team_column', type=str)
@click.argument('csv_grade_column', type=str)
@pass_course
@click.pass_context
def instructor_grading_load_grades(ctx, course, assignment_id, grade_component_id, csv_file, csv_team_column, csv_grade_column):   
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    grade_component = assignment.get_grade_component(grade_component_id)
    if not grade_component:
        print "Assignment %s does not have a grade component '%s'" % (assignment.id, grade_component)
        ctx.exit(CHISUBMIT_FAIL)
        
    csvf = csv.DictReader(csv_file)
            
    if csv_team_column not in csvf.fieldnames:
        print "CSV file %s does not have a '%s' column" % (csv_file, csv_team_column)
        ctx.exit(CHISUBMIT_FAIL)
        
    if csv_grade_column not in csvf.fieldnames:
        print "CSV file %s does not have a '%s' column" % (csv_file, csv_grade_column)
        ctx.exit(CHISUBMIT_FAIL)
            
    for entry in csvf:
        team_id = entry[csv_team_column]
        
        team = course.get_team(team_id)
        if team is None:
            print "%-40s SKIPPING. Not a team in course %s" % (team_id, course.id)
            continue

        ta = team.get_assignment(assignment_id)
        if ta is None:
            print "%-40s SKIPPING. Not registered for assignment %s" % (team_id, assignment_id)
            continue
        
        if ta.submitted_at is None:
            print "%-40s SKIPPING. Has not submitted assignment %s yet" % (team_id, assignment_id)
            continue
    
        grade = entry[csv_grade_column]
    
        if grade is None or grade == "":
            grade = 0
        else:
            grade = float(grade)

        if grade < 0 or grade > grade_component.points:
            print "%-40s SKIPPING. Invalid grade value %.2f (%s must be 0 <= x <= %.2f)" % (team_id, grade, grade_component_id, grade_component.points)
            continue
        
        try:
            team.set_assignment_grade(assignment_id, grade_component.id, grade)
            print "%-40s %s <- %.2f" % (team_id, grade_component_id, grade)
        except Exception:
            raise
            

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
            grades = student_grades[student.user.id][assignment.id]
            for gc in assignment.grade_components:
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
@click.option('--only-graders', type=str)
@click.option('--reset', is_flag=True)
@pass_course
@click.pass_context
def instructor_grading_assign_graders(ctx, course, assignment_id, from_assignment, avoid_assignment, only_graders, reset):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
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
    
    if only_graders is None:
        graders = course.graders[:]
    else:
        gd = {g.user.id: g for g in course.graders}
        only_graders = only_graders.strip().split(",")
        
        graders = []
        for g in only_graders:
            if g in gd:
                graders.append(gd[g])
            else:
                print "No such grader: %s" % g
                ctx.exit(CHISUBMIT_FAIL)        
    
    if len(graders) == 0:
        print "There are ZERO graders in this course!"
        ctx.exit(CHISUBMIT_FAIL)

    min_teams_per_grader = len(teams) / len(graders)
    extra_teams = len(teams) % len(graders)

    teams_per_grader = dict([(g.user.id, min_teams_per_grader) for g in graders])
    teams_per_grader_assigned = dict([(g.user.id, 0) for g in graders])
    
    random.seed(course.id + assignment_id)
    random.shuffle(graders)

    # so many graders in this course that some will end up expecting zero
    # teams to grade. Make sure they are able to get at least one.
    for g in graders[:extra_teams]:
        teams_per_grader[g.user.id] += 1

    team_grader = {t.id: None for t in teams}
    ta = {t.id: t.get_assignment(assignment.id) for t in teams}

    if from_assignment is not None:
        common_teams = [t for t in course.teams if t.has_assignment(assignment.id) and t.has_assignment(from_assignment.id)]
        for t in common_teams:
            team_assignment_from = t.get_assignment(from_assignment.id)

            # try to assign the same grader that would grade the same team's other assignment
            grader = team_assignment_from.grader
            if grader is not None and teams_per_grader[grader.user.id] > 0:
                team_grader[t.id] = grader.user.id 
                teams_per_grader[grader.user.id] -= 1
                teams_per_grader_assigned[grader.user.id] += 1

    if not reset:
        for t in teams:
            if ta[t.id].grader is None:
                team_grader[t.id] = None
            else:
                grader_id = ta[t.id].grader.id 
                team_grader[t.id] = grader_id
                teams_per_grader[grader_id] -= 1
                teams_per_grader_assigned[grader_id] += 1

    not_ready_for_grading = []
    ta_avoid = {}
    graders_cycle = itertools.cycle(graders)
    for t in teams:
        if team_grader[t.id] is not None:
            continue
        
        if not t.has_assignment_ready_for_grading(assignment):
            not_ready_for_grading.append(t.id)
            continue

        for g in graders_cycle:
            if teams_per_grader[g.user.id] == 0:
                continue
            else:
                if avoid_assignment is not None:
                    taa = ta_avoid.setdefault(t.id, t.get_assignment(avoid_assignment.id))
                    if taa.grader.user.id == grader.user.id:
                        continue
                
                valid = True
                for s in t.students:
                    conflicts = g.get_conflicts()
                    if s.user.id in conflicts:
                        valid = False
                        break

                if valid:
                    team_grader[t.id] = g.user.id 
                    teams_per_grader[g.user.id] -= 1
                    teams_per_grader_assigned[g.user.id] += 1                        
                    break                    

    for t in teams:
        if team_grader[t.id] is None:
            if t.id not in not_ready_for_grading:
                print "Team %s has no grader" % (t.id)
            else:
                print "Team %s's submission isn't ready for grading yet" % (t.id)
        else:
            if ta[t.id].grader !=  team_grader[t.id]:
                t.set_assignment_grader(assignment.id, team_grader[t.id])

    print 
    for grader_id, assigned in teams_per_grader_assigned.items():
        if teams_per_grader[grader_id] != 0:
            print grader_id, assigned, "(still needs to be assigned %i more assignments)" % (teams_per_grader[grader_id])
        else:
            print grader_id, assigned

    return CHISUBMIT_SUCCESS


@click.command(name="list-grader-assignments")
@click.argument('assignment_id', type=str)
@click.option('--grader-id', type=str)
@pass_course
@click.pass_context
def instructor_grading_list_grader_assignments(ctx, course, assignment_id, grader_id):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
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
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        ta = team.get_assignment(assignment.id)

        if ta.submitted_at is None:
            print "%25s NOT SUBMITTED" % team.id
        else:
            submission_commit = conn.get_commit(course, team, ta.commit_sha)
            if submission_commit is not None:
                if team.has_assignment_ready_for_grading(assignment):
                    print "%25s SUBMITTED (READY for grading)" % team.id
                else:
                    print "%25s SUBMITTED (NOT READY for grading)" % team.id
            else:
                print "%25s ERROR: Submitted but commit %s not found in repository" % (team.id, ta.commit_sha)
    
    return CHISUBMIT_SUCCESS


@click.command(name="show-grading-status")
@click.argument('assignment_id', type=str)
@click.option('--by-grader', is_flag=True)
@pass_course
@click.pass_context
def instructor_grading_show_grading_status(ctx, course, assignment_id, by_grader):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment)
    teams.sort(key=operator.attrgetter("id"))
    
    team_status = []
    graders = set()
    
    for team in teams:
        ta = team.get_assignment(assignment_id)
        grade_ids = [g.grade_component_id for g in ta.grades]

        if ta.grader is not None:
            grader_id = ta.grader.id
        else:
            grader_id = "<no grader assigned>"
            
        graders.add(grader_id)

        has_some = False
        has_all = True
        for gc in assignment.grade_components:
            if gc.id in grade_ids:
                has_some = True
            else:
                has_all = False

        if not has_some:
            team_status.append((team.id, grader_id, "NOT GRADED"))
        elif has_all:
            team_status.append((team.id, grader_id, "GRADED"))
        else:
            team_status.append((team.id, grader_id, "PARTIALLY GRADED"))

    if not by_grader:
        for team, grader, status in team_status:
            print "%-40s %-20s %s" % (team, status, grader)
    else:
        for grader in sorted(list(graders)):
            print grader
            print "-" * len(grader)
            
            team_status_grader = [ts for ts in team_status if ts[1] == grader]
            
            for team, _, status in team_status_grader:
                print "%-40s %s" % (team, status)

            print

    return CHISUBMIT_SUCCESS

@click.command(name="create-grading-repos")
@click.argument('assignment_id', type=str)
@click.option('--all-teams', is_flag=True)
@pass_course
@click.pass_context
def instructor_grading_create_grading_repos(ctx, course, assignment_id, all_teams):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, only_ready_for_grading=not all_teams)

    repos = create_grading_repos(ctx.obj['config'], course, assignment, teams)

    if repos == None:
        ctx.exit(CHISUBMIT_FAIL)

    return CHISUBMIT_SUCCESS


@click.command(name="create-grading-branches")
@click.argument('assignment_id', type=str)
@click.option('--all-teams', is_flag=True)
@click.option('--only', type=str)
@pass_course
@click.pass_context
def instructor_grading_create_grading_branches(ctx, course, assignment_id, all_teams, only):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, only = only, only_ready_for_grading=not all_teams)

    if teams is None:
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, assignment)

        if repo is None:
            print "%s does not have a grading repository" % team.id
            continue
        
        ta = team.get_assignment(assignment.id)

        if ta.submitted_at is None:
            print "Skipping grading branch. %s has not submitted." % team.id
        elif repo.has_grading_branch():
            print "Skipping grading branch. %s already has a grading branch." % team.id
        else:
            repo.create_grading_branch()
            print "Created grading branch for %s" % team.id

    return CHISUBMIT_SUCCESS


@click.command(name="push-grading-branches")
@click.argument('assignment_id', type=str)
@click.option('--to-staging', is_flag=True)
@click.option('--to-students', is_flag=True)
@click.option('--all-teams', is_flag=True)
@click.option('--only', type=str)
@pass_course
@click.pass_context
def instructor_grading_push_grading_branches(ctx, course, assignment_id, to_staging, to_students, all_teams, only):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, only = only, only_ready_for_grading=not all_teams)

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
        print "Assignment %s does not exist" % assignment_id
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
@click.option('--commit', is_flag=True)
@click.option('--all-teams', is_flag=True)
@pass_course
@click.pass_context
def instructor_grading_add_rubrics(ctx, course, assignment_id, commit, all_teams):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, only_ready_for_grading=not all_teams)

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, assignment)
        team_assignment = team.get_assignment(assignment_id)
        rubric = RubricFile.from_assignment(assignment, team_assignment)
        rubricfile = "%s.rubric.txt" % assignment.id
        rubricfilepath = "%s/%s" % (repo.repo_path, rubricfile)
        
        if commit:
            if not os.path.exists(rubricfilepath):
                rubric.save(rubricfilepath, include_blank_comments=True)
                rv = repo.commit([rubricfile], "Added grading rubric")
                if rv:
                    print rubricfilepath, "(COMMITTED)"
                else:
                    print rubricfilepath, "(NO CHANGES - Not committed)"
            else:
                print rubricfilepath, "(SKIPPED - already exists)"
        else:
            rubric.save(rubricfilepath, include_blank_comments=True)
            print rubricfilepath


@click.command(name="collect-rubrics")
@click.argument('assignment_id', type=str)
@click.option('--dry-run', is_flag=True)
@click.option('--grader-id', type=str)
@pass_course
@click.pass_context
def instructor_grading_collect_rubrics(ctx, course, assignment_id, dry_run, grader_id):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    if grader_id is not None:
        grader = course.get_grader(grader_id)
        if grader is None:
            print "Grader %s does not exist" % grader_id
            ctx.exit(CHISUBMIT_FAIL)
    else:
        grader = None

    gcs = assignment.grade_components

    teams = get_teams(course, assignment, grader=grader)

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, assignment)
        if repo is None:
            print "Repository for %s does not exist" % (team.id)
            continue

        rubricfile = repo.repo_path + "/%s.rubric.txt" % assignment.id

        if not os.path.exists(rubricfile):
            print "Repository for %s does not have a rubric for assignment %s" % (team.id, assignment.id)
            continue

        try:
            rubric = RubricFile.from_file(open(rubricfile), assignment)
        except ChisubmitRubricException, cre:
            print "ERROR: Rubric for %s does not validate (%s)" % (team.id, cre.message)
            continue

        points = []
        for gc in gcs:
            grade = rubric.points[gc.description]
            if grade is None:
                points.append(0.0)
            else:
                if not dry_run:
                    team.set_assignment_grade(assignment.id, gc.id, grade)
                points.append(grade)

        penalties = {}
        total_penalties = 0.0
        if rubric.penalties is not None:
            for desc, p in rubric.penalties.items():
                penalties[desc] = p
                total_penalties += p

        if not dry_run:
            team.set_assignment_penalties(assignment.id, penalties)

        if ctx.obj["verbose"]:
            print team.id
            print "+ %s" % points
            print "- %.2f" % total_penalties

        if not dry_run:
            new_team = course.get_team(team.id)
            assignment_team = new_team.get_assignment(assignment.id)
            total_grade = assignment_team.get_total_grade()
        else:
            total_grade = sum(points) + total_penalties
            
        if ctx.obj["verbose"]:
            print "TOTAL: %.2f" % total_grade
            print
        else:
            print "%-40s %.2f" % (team.id, total_grade)
            

instructor_grading.add_command(instructor_grading_set_grade)
instructor_grading.add_command(instructor_grading_load_grades)
instructor_grading.add_command(instructor_grading_list_grades)
instructor_grading.add_command(instructor_grading_assign_graders)
instructor_grading.add_command(instructor_grading_list_grader_assignments)
instructor_grading.add_command(instructor_grading_list_submissions)
instructor_grading.add_command(instructor_grading_show_grading_status)
instructor_grading.add_command(instructor_grading_create_grading_repos)
instructor_grading.add_command(instructor_grading_create_grading_branches)
instructor_grading.add_command(instructor_grading_push_grading_branches)
instructor_grading.add_command(instructor_grading_pull_grading_branches)
instructor_grading.add_command(instructor_grading_add_rubrics)
instructor_grading.add_command(instructor_grading_collect_rubrics)

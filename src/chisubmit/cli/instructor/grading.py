import click

from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.repos.grading import GradingGitRepo
from chisubmit.rubric import RubricFile, ChisubmitRubricException
from chisubmit.cli.common import create_grading_repos,\
    gradingrepo_push_grading_branch, gradingrepo_pull_grading_branch,\
    get_assignment_or_exit, get_teams_registrations, get_team_or_exit,\
    get_assignment_registration_or_exit, get_grader_or_exit,\
    catch_chisubmit_exceptions, require_local_config, validate_repo_rubric,\
    get_student_or_exit
from chisubmit.cli.common import pass_course
from chisubmit.common.utils import create_connection

import csv
import operator
import random
import itertools
import os.path
import yaml
from chisubmit.client.exceptions import UnknownObjectException
import math

@click.group(name="grading")
@click.pass_context
def instructor_grading(ctx):
    pass


@click.command(name="set-grade")
@click.argument('team_id', type=str)
@click.argument('assignment_id', type=str)
@click.argument('rubric_component_description', type=str)
@click.argument('points', type=float)
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_set_grade(ctx, course, team_id, assignment_id, rubric_component_description, points):   
    assignment = get_assignment_or_exit(ctx, course, assignment_id)
    team = get_team_or_exit(ctx, course, team_id)
    registration = get_assignment_registration_or_exit(ctx, team, assignment_id)
     
    rubric_components = assignment.get_rubric_components()
    
    rubric_component = [rc for rc in rubric_components if rc.description == rubric_component_description]
    
    if len(rubric_component) == 0:
        print "No such rubric component in %s: %s" % (assignment_id, rubric_component_description)
        ctx.exit(CHISUBMIT_FAIL)
    elif len(rubric_component) > 1:
        print "ERROR: Server returned more than one rubric component for '%s' in %s" % (rubric_component_description, assignment_id)
        print "       This should not happen. Please contact the chisubmit administrator."
        ctx.exit(CHISUBMIT_FAIL)
    else:
        rc = rubric_component[0]
        
        try:
            registration.set_grade(rc, points)
            ctx.exit(CHISUBMIT_SUCCESS)
        except ValueError, ve:
            print ve.message
            ctx.exit(CHISUBMIT_FAIL)
            


@click.command(name="load-grades")
@click.argument('assignment_id', type=str)
@click.argument('grade_component_id', type=str)
@click.argument('csv_file', type=click.File('rb'))
@click.argument('csv_team_column', type=str)
@click.argument('csv_grade_column', type=str)
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_load_grades(ctx, course, assignment_id, grade_component_id, csv_file, csv_team_column, csv_grade_column):   
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    grade_component = assignment.get_grade_component(grade_component_id)
    if not grade_component:
        print "Assignment %s does not have a grade component '%s'" % (assignment.assignment_id, grade_component)
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
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_add_conflict(ctx, course, grader_id, student_id):
    grader = get_grader_or_exit(ctx, course, grader_id)
    student = get_student_or_exit(ctx, course, student_id)

    if student.username in grader.conflicts_usernames:
        print "Student %s is already listed as a conflict for grader %s" % (student.username, grader.username)
        ctx.exit(CHISUBMIT_FAIL)

    conflicts_usernames = grader.conflicts_usernames[:]
    conflicts_usernames.append(student.username)
    grader.conflicts_usernames = conflicts_usernames

    return CHISUBMIT_SUCCESS

@click.command(name="list-grades")
@click.option('--detailed', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_list_grades(ctx, course, detailed):
    students = [s for s in course.get_students() if not s.dropped]
    assignments = course.get_assignments(include_rubric=True)

    students.sort(key=operator.attrgetter("user.last_name"))
    assignments.sort(key=operator.attrgetter("deadline"))

    student_grades = dict([(s.user.username,dict([(a.assignment_id,{}) for a in assignments])) for s in students])

    teams = course.get_teams(include_students=True, include_assignments=True, include_grades=True)

    for team in teams:
        registrations = team.get_assignment_registrations()
        for registration in registrations:
            assignment_id = registration.assignment.assignment_id
            for student in team.get_team_members():
                student_id = student.username
                if student_grades.has_key(student_id):
                    g = student_grades[student_id][assignment_id]
                    for grade in registration.get_grades():
                        rc_description = grade.rubric_component.description
                        if g.has_key(rc_description):
                            print "Warning: %s already has a grade for rubric component '%s'" % (student_id, rc_description)
                        else:
                            g[rc_description] = grade.points
                    g["__PENALTIES"] = registration.get_total_penalties()
                    g["__BONUSES"] = registration.get_total_bonuses()                    
                    g["__TOTAL"] = registration.get_total_grade()

    fields = ["Username","Last Name","First Name"]
    for assignment in assignments:
        if detailed:
            rubric_components = assignment.get_rubric_components()
            fields += ["%s - %s" % (assignment.assignment_id, rc.description) for rc in rubric_components]
            fields.append("%s - Penalties" % assignment.assignment_id)
            fields.append("%s - Bonuses" % assignment.assignment_id) 
            fields.append("%s - Total" % assignment.assignment_id)
        else:
            fields.append("%s" % assignment.assignment_id)

    print ",".join(fields)

    for student in students:
        fields = [student.user.username, student.user.last_name, student.user.first_name]
        for assignment in assignments:
            grades = student_grades[student.user.username][assignment.assignment_id]
            if detailed:
                rubric_components = assignment.get_rubric_components()
                for rc in rubric_components:
                    if not grades.has_key(rc.description):
                        fields.append("")
                    else:
                        fields.append(str(grades[rc.description]))
                if len(grades) == 0:
                    fields += ["","",""]
                else:
                    fields.append(str(grades["__PENALTIES"]))
                    fields.append(str(grades["__BONUSES"]))
                    fields.append(str(grades["__TOTAL"]))
            else:
                if len(grades) == 0:
                    fields.append("")
                else:
                    fields.append(str(grades["__TOTAL"]))

        print ",".join(fields)

@click.command(name="assign-grader")
@click.argument('assignment_id', type=str)
@click.argument('team_id', type=str)
@click.argument('grader_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_assign_grader(ctx, course, assignment_id, team_id, grader_id):
    team = get_team_or_exit(ctx, course, team_id)
    grader = get_grader_or_exit(ctx, course, grader_id)

    registration = get_assignment_registration_or_exit(ctx, team, assignment_id)

    registration.grader_username = grader.username

@click.command(name="assign-graders")
@click.argument('assignment_id', type=str)
@click.option('--from-assignment', type=str)
@click.option('--avoid-assignment', type=str)
@click.option('--grader-file', type=click.File('r'))
@click.option('--dry-run', is_flag=True)
@click.option('--reset', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_assign_graders(ctx, course, assignment_id, from_assignment, avoid_assignment, grader_file, dry_run, reset):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    if from_assignment is not None:
        from_assignment = get_assignment_or_exit(ctx, course, from_assignment)

    if avoid_assignment is not None:
        avoid_assignment = get_assignment_or_exit(ctx, course, avoid_assignment)

    if reset and from_assignment is not None:
        print "--reset and --from_assignment are mutually exclusive"
        ctx.exit(CHISUBMIT_FAIL)

    if avoid_assignment is not None and from_assignment is not None:
        print "--avoid_assignment and --from_assignment are mutually exclusive"
        ctx.exit(CHISUBMIT_FAIL)

    if grader_file is not None:
        grader_workload = yaml.load(grader_file)
        graders = []
        
        for username in grader_workload:
            try:
                grader = course.get_grader(username)
                graders.append(grader)
            except UnknownObjectException:
                print "No such grader: %s" % username
                ctx.exit(CHISUBMIT_FAIL)
    else:
        graders = course.get_graders()
        grader_workload = {g.user.username: "remainder" for g in graders}

    if len(graders) == 0:
        print "ERROR: No graders."
        ctx.exit(CHISUBMIT_FAIL)
            
    teams_registrations = get_teams_registrations(course, assignment)
    teams = teams_registrations.keys()

    n_teams = len(teams)
    teams_per_grader = {}
    teams_per_grader_assigned = dict([(g.user.username, 0) for g in graders])    
    assigned = 0
    graders_assigned_remainder = []
    for username, workload in grader_workload.items():
        if workload != "remainder":
            if not isinstance(workload, int) or workload <= 0:
                print "Invalid workload for grader '%s': %s" % (username, workload)
            teams_per_grader[username] = workload
            assigned += workload
        else:
            teams_per_grader[username] = None
            graders_assigned_remainder.append(username)
                        
    min_teams_per_grader = (n_teams - assigned) / len(graders_assigned_remainder)
    extra_teams = (n_teams - assigned) % len(graders_assigned_remainder)

    for username in teams_per_grader:
        if teams_per_grader[username] is None:
            teams_per_grader[username] = min_teams_per_grader
            
    random.seed(course.course_id + assignment_id)
    random.shuffle(graders_assigned_remainder)

    # so many graders in this course that some will end up expecting zero
    # teams to grade. Make sure they are able to get at least one.
    for username in graders_assigned_remainder[:extra_teams]:
        teams_per_grader[username] += 1
    
    assert sum([v for v in teams_per_grader.values()]) == n_teams

    team_grader = {t.team_id: None for t in teams_registrations.keys()}

    if from_assignment is not None:
        from_assignment_registrations = get_teams_registrations(course, from_assignment)
        
        common_teams = [t for t in teams if teams_registrations.has_key(t) and from_assignment_registrations.has_key(t)]
        for t in common_teams:
            registration = from_assignment_registrations[t]

            # try to assign the same grader that would grade the same team's other assignment
            grader = registration.grader
            if grader is not None and teams_per_grader[grader.user.username] > 0:
                team_grader[t.team_id] = grader.user.username 
                teams_per_grader[grader.user.username] -= 1
                teams_per_grader_assigned[grader.user.username] += 1

    if avoid_assignment is not None:
        avoid_assignment_registrations = get_teams_registrations(course, avoid_assignment)

    if not reset:
        for t in teams:
            if teams_registrations[t].grader is None:
                team_grader[t.team_id] = None
            else:
                grader_id = teams_registrations[t].grader.user.username
                team_grader[t.team_id] = grader_id
                teams_per_grader[grader_id] = max(0, teams_per_grader[grader_id] - 1)
                teams_per_grader_assigned[grader_id] += 1

    not_ready_for_grading = []
    ta_avoid = {}
    graders_cycle = itertools.cycle(graders)
    for team, registration in teams_registrations.items():
        if team_grader[team.team_id] is not None:
            continue

        if not registration.is_ready_for_grading():
            not_ready_for_grading.append(team.team_id)
            continue

        for g in graders_cycle:
            if teams_per_grader[g.user.username] == 0:
                continue
            else:
                if avoid_assignment is not None:
                    avoid_registration = ta_avoid.setdefault(team.team_id, avoid_assignment_registrations.get(team))
                    if avoid_registration is not None and avoid_registration.grader.user.username == grader.user.username:
                        continue
                
                valid = True
                for tm in team.get_team_members():
                    conflicts = g.conflicts
                    if tm.username in conflicts:
                        valid = False
                        break

                if valid:
                    team_grader[team.team_id] = g.user.username 
                    teams_per_grader[g.user.username] -= 1
                    teams_per_grader_assigned[g.user.username] += 1                        
                    break                    
    
    for team, registration in teams_registrations.items():
        if team_grader[team.team_id] is None:
            if team.team_id not in not_ready_for_grading:
                print "Team %s has no grader" % (team.team_id)
            else:
                print "Team %s's submission isn't ready for grading yet" % (team.team_id)
        else:
            if not dry_run:
                if registration.grader_username != team_grader[team.team_id]:
                    registration.grader_username = team_grader[team.team_id]
            else:
                print "%s: %s" % (team.team_id, team_grader[team.team_id])
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
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_list_grader_assignments(ctx, course, assignment_id, grader_id):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    if grader_id is not None:
        grader = get_grader_or_exit(ctx, course, grader_id)
    else:
        grader = None

    teams_registrations = get_teams_registrations(course, assignment)
    
    teams = teams_registrations.keys()
    teams.sort(key=operator.attrgetter("team_id"))

    for t in teams:
        registration = teams_registrations[t]
        if grader is None:
            if registration.grader is None:
                grader_str = "<no-grader-assigned>"
            else:
                grader_str = registration.grader.user.username
            print t.team_id, grader_str
        else:
            if grader == registration.grader.user.username:
                print t.team_id

    return CHISUBMIT_SUCCESS


@click.command(name="list-submissions")
@click.argument('assignment_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_list_submissions(ctx, course, assignment_id):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    teams_registrations = get_teams_registrations(course, assignment)
    teams = sorted(teams_registrations.keys(), key=operator.attrgetter("team_id"))

    conn = create_connection(course, ctx.obj['config'])
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        registration = teams_registrations[team]

        if registration.final_submission is None:
            print "%25s NOT SUBMITTED" % team.team_id
        else:
            submission_commit = conn.get_commit(course, team, registration.final_submission.commit_sha)
            if submission_commit is not None:
                if registration.is_ready_for_grading():
                    print "%25s SUBMITTED (READY for grading)" % team.team_id
                else:
                    print "%25s SUBMITTED (NOT READY for grading)" % team.team_id
            else:
                print "%25s ERROR: Submitted but commit %s not found in repository" % (team.team_id, registration.final_submission.commit_sha)
    
    return CHISUBMIT_SUCCESS


def print_grades_stats(grades):
    grades.sort()
    avg = sum(grades) / len(grades)
    stdev = math.sqrt(sum([(x-avg)**2 for x in grades])/len(grades))
    print
    print "     Average grade: %.2f" % avg
    print "Standard deviation: %.2f" % stdev
    print
    print "               Max: %.2f" % grades[-1]
    print "    Upper Quartile: %.2f" % grades[ int(len(grades)*0.75) ]
    print "            Median: %.2f" % grades[ int(len(grades)*0.5) ]
    print "    Lower Quartile: %.2f" % grades[ int(len(grades)*0.25) ]
    print "               Min: %.2f" % grades[0]
    print



@click.command(name="show-grading-status")
@click.argument('assignment_id', type=str)
@click.option('--by-grader', is_flag=True)
@click.option('--include-diff-urls', is_flag=True)
@click.option('--use-stored-grades', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_show_grading_status(ctx, course, assignment_id, by_grader, include_diff_urls, use_stored_grades):
    assignment = get_assignment_or_exit(ctx, course, assignment_id, include_rubric = True)
    rubric_components = assignment.get_rubric_components()

    teams_registrations = get_teams_registrations(course, assignment, include_grades = True)
    teams = sorted(teams_registrations.keys(), key=operator.attrgetter("team_id"))
    
    team_status = []
    graders = set()
    
    for team in teams:
        registration = teams_registrations[team]

        if registration.grader is None:
            grader_str = "<no grader assigned>"
        else:
            grader_str = registration.grader.user.username
        graders.add(grader_str)
        
        grading_status = None
        diff_url = ""
        
        if use_stored_grades:
            grades = registration.get_grades()
            total_grade = registration.get_total_grade()
            
            graded_rc_ids = [g.rubric_component_id for g in grades]            
        else:
            total_grade = 0.0
            repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, registration)
            if repo is None:
                grading_status = "NO GRADING REPO"
            else:
                rubricfile = repo.repo_path + "/%s.rubric.txt" % assignment.assignment_id
        
                if not os.path.exists(rubricfile):
                    grading_status = "NOT GRADED - No rubric"
                else:        
                    try:
                        rubric = RubricFile.from_file(open(rubricfile), assignment)

                        graded_rc_ids = [rc.id for rc in rubric_components if rubric.points_obtained[rc.description] is not None]  
                
                        total_grade = rubric.get_total_points_obtained()
                    except ChisubmitRubricException, cre:
                        grading_status = "ERROR: Rubric does not validate (%s)" % (cre.message)
                        
        if grading_status is None:
            has_some = False
            has_all = True
            for rc in rubric_components:
                if rc.id in graded_rc_ids:
                    has_some = True
                else:
                    has_all = False
                            
            if not has_some:
                grading_status = "NOT GRADED"
            elif has_all:
                grading_status = "GRADED"
            else:
                grading_status = "PARTIALLY GRADED"

            
            if include_diff_urls and has_some:
                commit_sha = registration.final_submission.commit_sha[:8]
                diff_url = "https://mit.cs.uchicago.edu/%s-staging/%s/compare/%s...%s-grading" % (course.course_id, team.team_id, commit_sha, assignment.assignment_id)
            
        team_status.append((team.team_id, grader_str, total_grade, diff_url, grading_status))

    if not by_grader:
        for team, grader, total_grade, diff_url, status in team_status:
            print "%-40s %-20s %-20.2f %10s  %s" % (team, status, total_grade, grader, diff_url)
    else:
        all_grades = []
        for grader in sorted(list(graders)):
            print grader
            print "-" * len(grader)
            
            grades = []
            
            team_status_grader = [ts for ts in team_status if ts[1] == grader]
            
            for team, _, total_grade, diff_url, status in team_status_grader:
                if status == "NOT GRADED":
                    print "%-40s %s  %s" % (team, status, diff_url)
                else:
                    print "%-40s %s %8.2f  %s" % (team, status, total_grade, diff_url)
                    if status == "GRADED":
                        grades.append(total_grade)
                        
            if len(grades) > 0:
                all_grades += grades
                print_grades_stats(grades)
            print

        if len(all_grades) > 0:
            print "TOTAL"
            print "-----"
            print_grades_stats(all_grades)

    return CHISUBMIT_SUCCESS

@click.command(name="create-grading-repos")
@click.argument('assignment_id', type=str)
@click.option('--all-teams', is_flag=True)
@click.option('--only', type=str)
@click.option('--master', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_create_grading_repos(ctx, course, assignment_id, all_teams, only, master):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)
    
    teams_registrations = get_teams_registrations(course, assignment, only = only, only_ready_for_grading=not all_teams)

    if len(teams_registrations) == 0:
        print "There are no grading repos to create."
        ctx.exit(CHISUBMIT_FAIL)
        
    teams = sorted(teams_registrations.keys(), key=operator.attrgetter("team_id"))

    for team in teams:
        registration = teams_registrations[team]
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, registration)
        
        if repo is None:
            print ("%40s -- Creating grading repo... " % team.team_id),
                
            repo = GradingGitRepo.create_grading_repo(ctx.obj['config'], course, team, registration, staging_only = not master)
            repo.sync()
            
            if registration.final_submission is not None:        
                if repo.has_grading_branch_staging():
                    if not registration.grading_started:
                        print "ERROR: This repo has a grading branch, but is not marked as ready for grading."
                    else:
                        gradingrepo_pull_grading_branch(ctx.obj['config'], course, team, registration)
                        print "done"
                else:
                    if master:
                        repo.create_grading_branch()
                        registration.grading_started = True
                        print "done (and created grading branch)"
                    else:
                        print "done (warning: could not pull grading branch; it does not exist)"
            else:
                if registration.grading_started:
                    print "ERROR: This team has not submitted this assignment, but the repo is marked as ready for grading."
                else:
                    print "done (note: has not submitted yet)"
        else:
            print ("%40s -- Updating grading repo... " % team.team_id),
            if repo.has_grading_branch_staging():
                if not registration.grading_started:
                    print "ERROR: This repo has a grading branch, but is not marked as ready for grading."
                else:                
                    gradingrepo_pull_grading_branch(ctx.obj['config'], course, team, registration)
                    print "done (pulled latest grading branch)"
            elif repo.has_grading_branch():
                print "nothing to update (grading branch is not in staging)"
            elif registration.final_submission is not None and master:
                repo.create_grading_branch()
                if not registration.grading_started:
                    registration.grading_started = True
                print "done (created missing grading branch)"
            else:
                print "nothing to update (there is no grading branch)"

    return CHISUBMIT_SUCCESS


@click.command(name="push-grading")
@click.argument('assignment_id', type=str)
@click.option('--to-students', is_flag=True)
@click.option('--all-teams', is_flag=True)
@click.option('--only', type=str)
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_push_grading(ctx, course, assignment_id, to_students, all_teams, only, yes):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    if to_students:
        print "You are going to push the grading branches to the student repositories."
        print "If you do so, students will be able to see their grading!"
        print 
        print "Are you sure you want to continue? (y/n): ", 
        
        if not yes:
            yesno = raw_input()
        else:
            yesno = 'y'
            print 'y'
            
        if yesno not in ('y', 'Y', 'yes', 'Yes', 'YES'):
            ctx.exit(CHISUBMIT_FAIL)
        print
    else:
        print "Pushing grading to staging repositories. Only instructors and graders will"
        print "be able to access this grading. If you want to push the grading to the"
        print "student repositories, use the --to-students option"
        print         
    
    teams_registrations = get_teams_registrations(course, assignment, only = only, only_ready_for_grading=not all_teams)
    teams = sorted(teams_registrations.keys(), key=operator.attrgetter("team_id"))

    for team in teams:
        registration = teams_registrations[team]
        print ("Pushing grading branch for team %s... " % team.team_id),
        gradingrepo_push_grading_branch(ctx.obj['config'], course, team, registration, to_students = to_students)
        print "done."

    return CHISUBMIT_SUCCESS



@click.command(name="pull-grading")
@click.argument('assignment_id', type=str)
@click.option('--from-students', is_flag=True)
@click.option('--only', type=str)
@click.option('--yes', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_pull_grading(ctx, course, assignment_id, from_students, only, yes):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)
    
    if from_students:
        print "Pulling grading from the student repositories is an uncommon operation."
        print "Instead, you should only ever make changes to the grading in the staging"
        print "repositories, and push those changes to the student repositories (which"
        print "should always mirror what is in the staging repositories). So, there should"
        print "never be a need to pull grading from a student repository."
        print 
        print "Are you sure you want to continue and pull the grading from"
        print "the student repositories? (y/n): ", 
        
        if not yes:
            yesno = raw_input()
        else:
            yesno = 'y'
            print 'y'
            
        if yesno not in ('y', 'Y', 'yes', 'Yes', 'YES'):
            ctx.exit(CHISUBMIT_FAIL)    
    
    teams_registrations = get_teams_registrations(course, assignment, only = only)
    teams = sorted(teams_registrations.keys(), key=operator.attrgetter("team_id"))

    for team in teams:
        registration = teams_registrations[team]
        print "Pulling grading branch for team %s... " % team.team_id
        gradingrepo_pull_grading_branch(ctx.obj['config'], course, team, registration, from_students = from_students)

    return CHISUBMIT_SUCCESS

@click.command(name="add-rubrics")
@click.argument('assignment_id', type=str)
@click.option('--commit', is_flag=True)
@click.option('--all-teams', is_flag=True)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_add_rubrics(ctx, course, assignment_id, commit, all_teams):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    teams_registrations = get_teams_registrations(course, assignment, only_ready_for_grading=not all_teams)
    teams = sorted(teams_registrations.keys(), key=operator.attrgetter("team_id"))

    for team in teams:
        registration = teams_registrations[team]
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, registration)
        
        if repo is None:
            print "%s does not have a grading repository" % team.team_id
            continue        
        
        rubric = RubricFile.from_assignment(assignment, registration.get_grades())
        rubricfile = "%s.rubric.txt" % assignment.assignment_id
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

@click.command(name="validate-rubrics")
@click.argument('assignment_id', type=str)
@click.option('--grader', type=str)
@click.option('--only', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_validate_rubrics(ctx, course, assignment_id, grader, only):
    if grader is not None:
        grader = get_grader_or_exit(ctx, course, grader)

    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    teams_registrations = get_teams_registrations(course, assignment, grader = grader, only = only)
    
    for team, registration in teams_registrations.items():
        valid, error_msg = validate_repo_rubric(ctx, course, assignment, team, registration)

        if valid:
            print "%s: Rubric OK." % team.team_id
        else:
            print "%s: Rubric ERROR: %s" % (team.team_id, error_msg)

    return CHISUBMIT_SUCCESS


@click.command(name="collect-rubrics")
@click.argument('assignment_id', type=str)
@click.option('--dry-run', is_flag=True)
@click.option('--only', type=str)
@click.option('--grader-id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_grading_collect_rubrics(ctx, course, assignment_id, dry_run, only, grader_id):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    if grader_id is not None:
        grader = get_grader_or_exit(ctx, course, grader_id)
    else:
        grader = None

    rcs = assignment.get_rubric_components()

    teams_registrations = get_teams_registrations(course, assignment, grader=grader, only=only)
    teams = sorted(teams_registrations.keys(), key=operator.attrgetter("team_id"))
    
    for team in teams:
        registration = teams_registrations[team]
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, registration)
        if repo is None:
            print "Repository for %s does not exist" % (team.team_id)
            continue

        rubricfile = repo.repo_path + "/%s.rubric.txt" % assignment.assignment_id

        if not os.path.exists(rubricfile):
            print "Repository for %s does not have a rubric for assignment %s" % (team.team_id, assignment.assignment_id)
            continue

        try:
            rubric = RubricFile.from_file(open(rubricfile), assignment)
        except ChisubmitRubricException, cre:
            print "ERROR: Rubric for %s does not validate (%s)" % (team.team_id, cre.message)
            continue

        points = []
        for rc in rcs:
            grade = rubric.points_obtained[rc.description]
            if grade is None:
                points.append(0.0)
            else:
                if not dry_run:
                    registration.set_grade(rc, grade)
                points.append(grade)

        adjustments = {}
        total_penalties = 0.0
        total_bonuses = 0.0
        if rubric.penalties is not None:
            for desc, p in rubric.penalties.items():
                adjustments[desc] = p
                total_penalties += p

        if rubric.bonuses is not None:
            for desc, p in rubric.bonuses.items():
                adjustments[desc] = p
                total_bonuses += p

        if not dry_run:
            registration.grade_adjustments = adjustments

        if ctx.obj["verbose"]:
            print team.team_id
            print "Points Obtained: %s" % points
            print "Penalties: %.2f" % total_penalties
            print "Bonuses: %.2f" % total_bonuses

        if not dry_run:
            total_grade = registration.get_total_grade()
        else:
            total_grade = sum(points) + total_penalties + total_bonuses
            
        if ctx.obj["verbose"]:
            print "TOTAL: %.2f" % total_grade
            print
        else:
            print "%-40s %.2f" % (team.team_id, total_grade)
            

instructor_grading.add_command(instructor_grading_set_grade)
instructor_grading.add_command(instructor_grading_load_grades)
instructor_grading.add_command(instructor_grading_list_grades)
instructor_grading.add_command(instructor_grading_assign_grader)
instructor_grading.add_command(instructor_grading_assign_graders)
instructor_grading.add_command(instructor_grading_add_conflict)
instructor_grading.add_command(instructor_grading_list_grader_assignments)
instructor_grading.add_command(instructor_grading_list_submissions)
instructor_grading.add_command(instructor_grading_show_grading_status)
instructor_grading.add_command(instructor_grading_create_grading_repos)
instructor_grading.add_command(instructor_grading_push_grading)
instructor_grading.add_command(instructor_grading_pull_grading)
instructor_grading.add_command(instructor_grading_add_rubrics)
instructor_grading.add_command(instructor_validate_rubrics)
instructor_grading.add_command(instructor_grading_collect_rubrics)

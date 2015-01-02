import click

from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
import operator
import random
from chisubmit.repos.grading import GradingGitRepo
import os.path
from chisubmit.rubric import RubricFile
from chisubmit.cli.common import create_grading_repos, get_teams,\
    gradingrepo_push_grading_branch, gradingrepo_pull_grading_branch
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory
from chisubmit.cli.common import pass_course

@click.group(name="grading")
@click.pass_context
def admin_grading(ctx):
    pass

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
    projects = course.projects

    students.sort(key=operator.attrgetter("last_name"))
    projects.sort(key=operator.attrgetter("deadline"))

    student_grades = dict([(s,dict([(p,None) for p in projects])) for s in students])

    for team in course.teams:
        for team_project in team.projects:
            for student in team.students:
                if student_grades.has_key(student):
                    if student_grades[student][team_project.project] is not None:
                        print "Warning: %s already has a grade"
                    else:
                        student_grades[student][team_project.project] = team_project

    fields = ["Last Name","First Name"]
    for project in projects:
        fields += ["%s - %s" % (project.id, gc.name) for gc in project.grade_components]
        fields.append("%s - Penalties" % project.id)
        fields.append("%s - Total" % project.id)

    print ",".join(fields)

    for student in students:
        fields = [student.last_name, student.first_name]
        for project in projects:
            for gc in project.grade_components:
                if student_grades[student][project] is None:
                    fields.append("")
                elif student_grades[student][project].grades is None:
                    fields.append("")
                elif not student_grades[student][project].grades.has_key(gc):
                    fields.append("")
                else:
                    fields.append(str(student_grades[student][project].grades[gc]))
            if student_grades[student][project] is None:
                fields += ["",""]
            else:
                fields.append(str(student_grades[student][project].get_total_penalties()))
                fields.append(str(student_grades[student][project].get_total_grade()))

        print ",".join(fields)


@click.command(name="assign-graders")
@click.argument('project_id', type=str)
@click.option('--fromproject', type=str)
@click.option('--avoidproject', type=str)
@click.option('--reset', is_flag=True)
@pass_course
@click.pass_context
def instructor_grading_assign_graders(ctx, course, project_id, fromproject, avoidproject, reset):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist" % project_id
        ctx.exit(CHISUBMIT_FAIL)

    from_project = None
    if fromproject is not None:
        from_project = course.get_project(fromproject)
        if from_project is None:
            print "Project %s does not exist" % from_project
            ctx.exit(CHISUBMIT_FAIL)

    avoid_project = None
    if avoidproject is not None:
        avoid_project = course.get_project(avoidproject)
        if avoid_project is None:
            print "Project %s does not exist" % avoid_project
            ctx.exit(CHISUBMIT_FAIL)

    if reset and fromproject is not None:
        print "--reset and --fromproject are mutually exclusive"
        ctx.exit(CHISUBMIT_FAIL)

    if avoidproject is not None and fromproject is not None:
        print "--avoidproject and --fromproject are mutually exclusive"
        ctx.exit(CHISUBMIT_FAIL)

    teams = [t for t in course.teams if t.has_project(project.id)]
    graders = course.graders

    if not graders:
        print "There are ZERO graders in this course!"
        ctx.exit(CHISUBMIT_FAIL)

    min_teams_per_grader = len(teams) / len(course.graders)
    extra_teams = len(teams) % len(course.graders)

    teams_per_grader = dict([(g.id, min_teams_per_grader) for g in course.graders])
    random.shuffle(graders)

    # so many graders in this course that some will end up expecting zero
    # teams to grade. Make sure they are able to get at least one.
    for g in graders[:extra_teams]:
        teams_per_grader[g.id] += 1

    if from_project is not None:
        common_teams = [t for t in course.teams if t.has_project(project.id) and t.has_project(from_project.id)]
        for t in common_teams:
            team_project_from = t.get_project(from_project.id)
            team_project_to = t.get_project(project.id)

            # try to assign the same grader that would grade the same team's other project
            grader = team_project_from.get_grader()
            if grader is not None and teams_per_grader[grader.id] > 0:
                team_project_to.grader = grader
                teams_per_grader[grader.id] -= 1

    if reset:
        for t in teams:
            t.get_project(project.id).grader = None

    for g in graders:
        if teams_per_grader[g.id] > 0:
            for t in teams:
                team_project = t.get_project(project.id)

                if avoid_project is not None:
                    team_project_avoid = t.get_project(avoid_project.id)
                    if team_project_avoid.get_grader() == grader:
                        continue

                team_project_grader = team_project.get_grader()
                if team_project_grader is None:
                    valid = True

                    # FIXME 16DEC14: grader conflicts
                    """for s in t.students:
                        if s in g.conflicts:
                            valid = False
                            break"""

                    if valid:
                        team_project.add_grader(g)
                        teams_per_grader[g.id] -= 1
                        if teams_per_grader[g.id] == 0:
                            break

    for g in graders:
        if teams_per_grader[g.id] != 0:
            print "Unable to assign enough teams to grader %s" % g.id

    for t in teams:
        team_project = t.get_project(project.id)
        if team_project.get_grader() is None:
            print "Team %s has no grader" % (t.id)

    return CHISUBMIT_SUCCESS


@click.command(name="list-grader-assignments")
@click.argument('project_id', type=str)
@click.option('--grader-id', type=str)
@pass_course
@click.pass_context
def instructor_grading_list_grader_assignments(ctx, course, project_id, grader_id):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist" % project_id
        ctx.exit(CHISUBMIT_FAIL)

    if grader_id is not None:
        grader = course.get_grader(grader_id)
        if grader is None:
            print "Grader %s does not exist" % grader_id
            ctx.exit(CHISUBMIT_FAIL)
    else:
        grader = None

    teams = [t for t in course.teams if t.has_project(project.id)]
    teams.sort(key=operator.attrgetter("id"))

    for t in teams:
        team_project = t.get_project(project.id)
        if grader is None:
            if team_project.get_grader() is None:
                grader_str = "<no-grader-assigned>"
            else:
                grader_str = team_project.get_grader().id
            print t.id, grader_str
        else:
            if grader == team_project.get_grader():
                print t.id

    return CHISUBMIT_SUCCESS


@click.command(name="list-submissions")
@click.argument('project_id', type=str)
@pass_course
@click.pass_context
def instructor_grading_list_submissions(ctx, course, project_id):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = [t for t in course.teams if t.has_project(project.id)]
    teams.sort(key=operator.attrgetter("id"))

    conn = RemoteRepositoryConnectionFactory.create_connection(course.git_server_connection_string)
    server_type = conn.get_server_type_name()
    git_credentials = ctx.obj['config']['git-credentials']

    if git_credentials is None:
        print "You do not have %s credentials." % server_type
        ctx.exit(CHISUBMIT_FAIL)

    conn.connect(git_credentials)

    for team in teams:
        submission_tag = conn.get_submission_tag(course, team, project.id)

        if submission_tag is None:
            print "%25s NOT SUBMITTED" % team.id
        else:
            print "%25s SUBMITTED" % team.id

    return CHISUBMIT_SUCCESS

@click.command(name="create-grading-repos")
@click.argument('project_id', type=str)
@pass_course
@click.pass_context
def instructor_grading_create_grading_repos(ctx, course, project_id):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = [t for t in course.teams if t.has_project(project.id)]

    repos = create_grading_repos(ctx.obj['config']['directory'], course, project, teams)

    if repos == None:
        ctx.exit(CHISUBMIT_FAIL)

    return CHISUBMIT_SUCCESS


@click.command(name="create-grading-branches")
@click.argument('project_id', type=str)
@click.option('--only', type=str)
@pass_course
@click.pass_context
def instructor_grading_create_grading_branches(ctx, course, project_id, only):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, project, only = only)

    if teams is None:
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(ctx['config']['directory'], course, team, project)

        if repo is None:
            print "%s does not have a grading repository" % team.id
            continue

        repo.create_grading_branch()
        print "Created grading branch for %s" % team.id

    return CHISUBMIT_SUCCESS


@click.command(name="push-grading-branches")
@click.argument('project_id', type=str)
@click.option('--staging', is_flag=True)
@click.option('--github', is_flag=True)
@click.option('--only', type=str)
@pass_course
@click.pass_context
def instructor_grading_push_grading_branches(ctx, course, project_id, staging, github, only):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, project, only = only)

    if teams is None:
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        print ("Pushing grading branch for team %s... " % team.id),
        gradingrepo_push_grading_branch(course, team, project, staging = staging, github = github)
        print "done."

    return CHISUBMIT_SUCCESS



@click.command(name="pull-grading-branches")
@click.argument('project_id', type=str)
@click.option('--staging', is_flag=True)
@click.option('--github', is_flag=True)
@click.option('--only', type=str)
@pass_course
@click.pass_context
def instructor_grading_pull_grading_branches(ctx, course, project_id, staging, github, only):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, project, only = only)

    if teams is None:
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        print "Pulling grading branch for team %s... " % team.id
        gradingrepo_pull_grading_branch(course, team, project, staging = staging, github = github)

    return CHISUBMIT_SUCCESS



@click.command(name="add-rubrics")
@click.argument('project_id', type=str)
@pass_course
@click.pass_context
def instructor_grading_add_rubrics(ctx, course, project_id):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist" % project_id
        ctx.exit(CHISUBMIT_FAIL)

    teams = [t for t in course.teams if t.has_project(project.id)]

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config']['directory'], course, team, project)
        rubric = RubricFile.from_assignment(project, team)
        rubricfile = repo.repo_path + "/%s.rubric.txt" % project.id
        rubric.save(rubricfile, include_blank_comments=True)


@click.command(name="collect-rubrics")
@click.argument('project_id', type=str)
@pass_course
@click.pass_context
def instructor_grading_collect_rubrics(ctx, course, project_id):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist" % project_id
        ctx.exit(CHISUBMIT_FAIL)

    gcs = project.grade_components

    teams = [t for t in course.teams if t.has_project(project.id)]

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config']['directory'], course, team, project)
        if repo is None:
            print "Repository for %s does not exist" % (team.id)
            ctx.exit(CHISUBMIT_FAIL)

        rubricfile = repo.repo_path + "/%s.rubric.txt" % project.id

        if not os.path.exists(rubricfile):
            print "Repository for %s does not have a rubric for project %s" % (team.id, project.id)
            ctx.exit(CHISUBMIT_FAIL)

        rubric = RubricFile.from_file(open(rubricfile), project)

        points = []
        for gc in gcs:
            if rubric.points[gc.name] is None:
                team.get_project(project.id).grades[gc] = 0
                points.append("")
            else:
                team.get_project(project.id).set_grade(gc, rubric.points[gc.name])
                points.append(`rubric.points[gc.name]`)

        team.get_project(project.id).penalties = []
        if rubric.penalties is not None:
            for desc, p in rubric.penalties.items():
                team.get_project(project.id).add_penalty(desc, p)

        print "%s: %s" % (team.id, team.get_project(project.id).get_total_grade())


admin_grading.add_command(instructor_grading_list_grades)
admin_grading.add_command(instructor_grading_assign_graders)
admin_grading.add_command(instructor_grading_list_grader_assignments)
admin_grading.add_command(instructor_grading_list_submissions)
admin_grading.add_command(instructor_grading_create_grading_repos)
admin_grading.add_command(instructor_grading_create_grading_branches)
admin_grading.add_command(instructor_grading_push_grading_branches)
admin_grading.add_command(instructor_grading_pull_grading_branches)
admin_grading.add_command(instructor_grading_add_rubrics)
admin_grading.add_command(instructor_grading_collect_rubrics)

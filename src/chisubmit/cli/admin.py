
#  Copyright (c) 2013-2014, The University of Chicago
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  - Neither the name of The University of Chicago nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.

from chisubmit.common.utils import create_subparser
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
import operator
import random
from chisubmit.core.repos import GradingGitRepo, GithubConnection
import os.path
from chisubmit.core.rubric import RubricFile, ChisubmitRubricException
from chisubmit.core import ChisubmitException, handle_unexpected_exception
from chisubmit.cli.common import create_grading_repos, get_teams,\
    gradingrepo_push_grading_branch, gradingrepo_pull_grading_branch
import chisubmit.core

def create_admin_subparsers(subparsers):
    subparser = create_subparser(subparsers, "admin-assign-project", cli_do__admin_assign_project)
    subparser.add_argument('project_id', type=str)
    subparser.add_argument('--force', action="store_true")

    subparser = create_subparser(subparsers, "admin-assign-graders", cli_do__admin_assign_graders)
    subparser.add_argument('project_id', type=str)
    subparser.add_argument('--fromproject', type=str)
    subparser.add_argument('--reset', action="store_true")

    subparser = create_subparser(subparsers, "admin-list-grader-assignments", cli_do__admin_list_grader_assignments)
    subparser.add_argument('project_id', type=str)
    subparser.add_argument('--grader', type=str)

    subparser = create_subparser(subparsers, "admin-list-submissions", cli_do__admin_list_submissions)
    subparser.add_argument('project_id', type=str)
    
    subparser = create_subparser(subparsers, "admin-create-grading-repos", cli_do__admin_create_grading_repos)
    subparser.add_argument('project_id', type=str)
    
    subparser = create_subparser(subparsers, "admin-create-grading-branches", cli_do__admin_create_grading_branches)
    subparser.add_argument('project_id', type=str)    
    subparser.add_argument('--only', type=str)    

    subparser = create_subparser(subparsers, "admin-pull-grading-branches", cli_do__admin_pull_grading_branches)
    subparser.add_argument('project_id', type=str)    
    subparser.add_argument('--staging', action="store_true")
    subparser.add_argument('--github', action="store_true")
    subparser.add_argument('--only', type=str)

    subparser = create_subparser(subparsers, "admin-push-grading-branches", cli_do__admin_push_grading_branches)
    subparser.add_argument('project_id', type=str)    
    subparser.add_argument('--staging', action="store_true")
    subparser.add_argument('--github', action="store_true")
    subparser.add_argument('--only', type=str)

    subparser = create_subparser(subparsers, "admin-create-rubric-files", cli_do__admin_add_rubrics)
    subparser.add_argument('project_id', type=str)

    subparser = create_subparser(subparsers, "admin-collect-rubrics", cli_do__admin_collect_rubrics)
    subparser.add_argument('project_id', type=str)



def cli_do__admin_assign_project(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist" % args.project_id
        return CHISUBMIT_FAIL
    
    teams = [t for t in course.teams.values() if t.active]
    
    teams_notactive = [t for t in course.teams.values() if not t.active]
    
    for t in teams_notactive:
        print "Skipping %s (not active)" % t.id
    
    for t in teams:
        if t.has_project(project.id) and not args.force:
            print "Team %s has already been assigned project %s. Use --force to override" % (t.id, project.id)
            continue
        
        t.add_project(project)
        print "Assigned project %s to team %s" % (project.id, t.id)
            

    
def cli_do__admin_assign_graders(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist" % args.project_id
        return CHISUBMIT_FAIL

    from_project = None
    if args.fromproject is not None:
        from_project = course.get_project(args.fromproject)
        if from_project is None:
            print "Project %s does not exist" % from_project
            return CHISUBMIT_FAIL
        
    if args.reset and args.fromproject is not None:
        print "--reset and --fromproject are mutually exclusive"
        return CHISUBMIT_FAIL
    
    teams = [t for t in course.teams.values() if t.has_project(project.id)]
    graders = course.graders.values()
    
    min_teams_per_grader = len(teams) / len(course.graders)
    extra_teams = len(teams) % len(course.graders)
    
    teams_per_grader = dict([(g, min_teams_per_grader) for g in course.graders.values()])
    random.shuffle(graders)
    
    for g in graders[:extra_teams]:
        teams_per_grader[g] += 1    
    
    if from_project is not None:
        common_teams = [t for t in course.teams.values() if t.has_project(project.id) and t.has_project(from_project.id)]
        for t in common_teams:
            team_project_from =  t.get_project(from_project.id)
            team_project_to =  t.get_project(project.id)

            grader = team_project_from.grader
            if grader is not None and teams_per_grader[grader] > 0:           
                team_project_to.grader = grader 
                teams_per_grader[grader] -= 1
        
    for g in graders:
        if teams_per_grader[g] > 0:
            for t in teams:
                team_project =  t.get_project(project.id)
                if team_project.grader is None or args.reset:
                    valid = True
                    
                    for s in t.students:
                        if s in g.conflicts:
                            valid = False
                            break
                        
                    if valid:
                        team_project.grader = g
                        teams_per_grader[g] -= 1
                        if teams_per_grader[g] == 0:
                            break
                    
    for g in graders:
        if teams_per_grader[g] != 0:
            print "Unable to assign enough teams to grader %s" % g.id
            
    for t in teams:
        team_project =  t.get_project(project.id)
        if team_project.grader is None:
            print "Team %s has no grader" % (t.id)
            
    return CHISUBMIT_SUCCESS

                
def cli_do__admin_list_grader_assignments(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    if args.grader is not None:
        grader = course.get_grader(args.grader)
        if grader is None:
            print "Grader %s does not exist" % args.grader_id
            return CHISUBMIT_FAIL
    else:
        grader = None
        
    teams = [t for t in course.teams.values() if t.has_project(project.id)]
    teams.sort(key=operator.attrgetter("id"))
    
    for t in teams:
        team_project = t.get_project(project.id)
        if grader is None:
            if team_project.grader is None:
                grader_str = "<no-grader-assigned>"
            else:
                grader_str = team_project.grader.id
            print t.id, grader_str
        else:
            if grader == team_project.grader:
                print t.id
                
    return CHISUBMIT_SUCCESS
                
def cli_do__admin_list_submissions(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
        
    teams = [t for t in course.teams.values() if t.has_project(project.id)]
    teams.sort(key=operator.attrgetter("id"))        
        
    github_access_token = chisubmit.core.get_github_token()

    if github_access_token is None:
        print "You have not created a GitHub access token."
        print "You can create one using 'chisubmit gh-token-create'"
        return CHISUBMIT_FAIL    
            
    try:
        gh = GithubConnection(github_access_token, course.github_organization)
            
        for team in teams:
            submission_tag = gh.get_submission_tag(team, project.id)
            
            if submission_tag is None:
                print "%25s NOT SUBMITTED" % team.id
            else:
                print "%25s SUBMITTED" % team.id
            
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
                
    return CHISUBMIT_SUCCESS                
                
def cli_do__admin_create_grading_repos(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    teams = [t for t in course.teams.values() if t.has_project(project.id)]
    
    repos = create_grading_repos(course, project, teams)
    
    if repos == None:
        return CHISUBMIT_FAIL
    
    return CHISUBMIT_SUCCESS
                  
                  
def cli_do__admin_create_grading_branches(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    teams = get_teams(course, project, only = args.only)
    
    if teams is None:
        return CHISUBMIT_FAIL
    
    for team in teams:
        try:
            repo = GradingGitRepo.get_grading_repo(course, team, project)
            
            if repo is None:
                print "%s does not have a grading repository" % team.id
                continue
            
            try:
                repo.create_grading_branch()
                print "Created grading branch for %s" % team.id
            except ChisubmitException, ce:
                print "Could not create grading branch for %s: %s" % (team.id, ce.message)
        except ChisubmitException, ce:
            raise ce # Propagate upwards, it will be handled by chisubmit_cmd
        except Exception, e:
            handle_unexpected_exception()    
    
    return CHISUBMIT_SUCCESS


def cli_do__admin_push_grading_branches(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    teams = get_teams(course, project, only = args.only)
    
    if teams is None:
        return CHISUBMIT_FAIL
        
    for team in teams:
        print ("Pushing grading branch for team %s... " % team.id), 
        gradingrepo_push_grading_branch(course, team, project, staging = args.staging, github = args.github)
        print "done."
        
    return CHISUBMIT_SUCCESS


def cli_do__admin_pull_grading_branches(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    teams = get_teams(course, project, only = args.only)
    
    if teams is None:
        return CHISUBMIT_FAIL
        
    for team in teams:
        print "Pulling grading branch for team %s... " % team.id
        gradingrepo_pull_grading_branch(course, team, project, staging = args.staging, github = args.github)

    return CHISUBMIT_SUCCESS



def cli_do__admin_add_rubrics(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist" % args.project_id
        return CHISUBMIT_FAIL
    
    teams = [t for t in course.teams.values() if t.has_project(project.id)]
    
    for team in teams:
        team_project = team.get_project(project.id)
        try:    
            repo = GradingGitRepo.get_grading_repo(course, team, project)
            
            rubric = RubricFile.from_project(project, team_project)
            rubricfile = repo.repo_path + "/%s.rubric.txt" % project.id
            rubric.save(rubricfile, include_blank_comments=True)            
        except ChisubmitException, ce:
            raise ce # Propagate upwards, it will be handled by chisubmit_cmd
        except Exception, e:
            handle_unexpected_exception()
                

def cli_do__admin_collect_rubrics(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist" % args.project_id
        return CHISUBMIT_FAIL

    gcs = [gc.name for gc in project.grade_components]

    print "team," + ",".join(gcs)
    
    teams = [t for t in course.teams.values() if t.has_project(project.id)]

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(course, team, project)
        if repo is None:    
            print "Repository for %s does not exist" % (team.id)
            return CHISUBMIT_FAIL
            
        rubricfile = repo.repo_path + "/%s.rubric.txt" % project.id
        
        if not os.path.exists(rubricfile):
            print "Repository for %s does not have a rubric for project %s" % (team.id, project.id)
            return CHISUBMIT_FAIL
        
        try:
            rubric = RubricFile.from_file(open(rubricfile), project)
        except ChisubmitRubricException, cre:
            print "Error in rubric: %s" % cre.message
            return CHISUBMIT_FAIL

        points = []
        for gc in gcs:
            if rubric.points[gc] is None:
                points.append("")
            else:
                points.append(`rubric.points[gc]`)

        print "%s,%s" % (team.id, ",".join(points))
                
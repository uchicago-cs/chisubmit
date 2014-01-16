
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
from chisubmit.core.repos import GradingGitRepo
import os.path
from chisubmit.core.rubric import RubricFile, ChisubmitRubricException

def create_admin_subparsers(subparsers):
    subparser = create_subparser(subparsers, "admin-assign-graders", cli_do__admin_assign_graders)
    subparser.add_argument('project_id', type=str)

    subparser = create_subparser(subparsers, "admin-list-grader-assignments", cli_do__admin_list_grader_assignments)
    subparser.add_argument('project_id', type=str)
    subparser.add_argument('--grader', type=str)

    subparser = create_subparser(subparsers, "admin-collect-rubrics", cli_do__admin_collect_rubrics)
    subparser.add_argument('project_id', type=str)

    
def cli_do__admin_assign_graders(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist" % args.project_id
        return CHISUBMIT_FAIL
    
    teams = [t for t in course.teams.values() if t.has_project(project.id)]
    graders = course.graders.values()
    
    min_teams_per_grader = len(teams) / len(course.graders)
    extra_teams = len(teams) % len(course.graders)
    
    teams_per_grader = dict([(g, min_teams_per_grader) for g in course.graders.values()])
    random.shuffle(graders)
    
    for g in graders[:extra_teams]:
        teams_per_grader[g] += 1
        
    for g in graders:
        for t in teams:
            team_project =  t.get_project(project.id)
            if team_project.grader is None:
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
                

def cli_do__admin_collect_rubrics(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist" % args.project_id
        return CHISUBMIT_FAIL

    gcs = [gc.name for gc in project.grade_components]

    print "team," + ",".join(gcs)
    
    teams = [t for t in course.teams.values() if t.has_project(project.id)]

    for team in teams:
        team_project = team.get_project(project.id)

        repo = GradingGitRepo.get_grading_repo(course, team)
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
        
        
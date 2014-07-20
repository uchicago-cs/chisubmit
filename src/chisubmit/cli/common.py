import click

from chisubmit.core.repos import GradingGitRepo
from chisubmit.core import ChisubmitException, handle_unexpected_exception
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS

from functools import update_wrapper

def pass_course(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        if ctx.obj["course_obj"] is None:
            if not ctx.obj["course_specified"]:
                raise click.UsageError("No course specified with --course and there is no default course")
            else:
                raise click.UsageError("Unexpected error. A course has been specified with --course, but not course object has been loaded.")
            
        return ctx.invoke(f, ctx.obj["course_obj"], *args, **kwargs)
        
    return update_wrapper(new_func, f)


def save_changes(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        ctx.call_on_close(ctx.obj["course_obj"].save)
            
        return ctx.invoke(f, *args, **kwargs)
        
    return update_wrapper(new_func, f)
    

def get_teams(course, project, grader = None, only = None):
    if only is not None:
        team = course.get_team(only)
        if team is None:
            print "Team %s does not exist"
            return None
        if not team.has_project(project.id):
            print "Team %s has not been assigned project %s" % (team.id, project.id)
            return None
        
        teams = [team]
    else:
        teams = [t for t in course.teams.values() if t.has_project(project.id)]  
        
        if grader is not None:
            teams = [t for t in teams if t.get_project(project.id).grader == grader]        

    return teams  


def create_grading_repos(course, project, teams, grader = None):
    repos = []
   
    for team in teams:
        try:
            repo = GradingGitRepo.get_grading_repo(course, team, project)
            
            if repo is None:
                print ("Creating grading repo for %s... " % team.id),
                repo = GradingGitRepo.create_grading_repo(course, team, project)
                repo.sync()
                
                repos.append(repo)
                
                print "done"
            else:
                print "Grading repo for %s already exists" % team.id
        except ChisubmitException, ce:
            raise ce # Propagate upwards, it will be handled by chisubmit_cmd
        except Exception, e:
            handle_unexpected_exception()
            
    return repos
            

def gradingrepo_push_grading_branch(course, team, project, github=False, staging=False):
    try:    
        repo = GradingGitRepo.get_grading_repo(course, team, project)
        
        if repo is None:
            print "%s does not have a grading repository" % team.id
            return CHISUBMIT_FAIL
        
        if not repo.has_grading_branch():
            print "%s does not have a grading branch" % team.id
            return CHISUBMIT_FAIL 
            
        if github:
            repo.push_grading_branch_to_github()
            
        if staging:
            repo.push_grading_branch_to_staging()
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()

    return CHISUBMIT_SUCCESS

def gradingrepo_pull_grading_branch(course, team, project, github=False, staging=False):
    assert(not (github and staging))
    try:
        repo = GradingGitRepo.get_grading_repo(course, team, project)
        
        if repo is None:
            print "%s does not have a grading repository" % team.id
            return CHISUBMIT_FAIL
       
        if github:
            if not repo.has_grading_branch_staging():
                print "%s does not have a grading branch on GitHub" % team.id
            else:
                repo.pull_grading_branch_from_github()
        
        if staging:
            if not repo.has_grading_branch_staging():
                print "%s does not have a grading branch in staging" % team.id
            else:
                repo.pull_grading_branch_from_staging()
            
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS                
from github import Github, InputGitAuthor
from github.GithubException import GithubException

import git
import os.path
import pytz
from datetime import datetime

import chisubmit.core
from chisubmit.core import ChisubmitException
from git.exc import GitCommandError

class GithubConnection(object):
    def __init__(self, access_token, organization):
        self.gh = Github(access_token)

        try:
            self.organization = self.gh.get_organization(organization)
        except GithubException as ge:
            if ge.status == 401:
                raise ChisubmitException("Invalid Github Credentials", ge)
            elif ge.status == 404:
                raise ChisubmitException("Organization %s does not exist" % organization, ge)            
            else:
                raise ChisubmitException("Unexpected error accessing organization %s (%i: %s)" % (organization, ge.status, ge.data["message"]), ge)            

    def create_team_repository(self, course, team, fail_if_exists=True, private=True):
        repo_name = "%s-%s" % (course.id, team.id)
        team_name = repo_name
        student_names = ", ".join(["%s %s" % (s.first_name, s.last_name) for s in team.students])
        repo_description = "%s: Team %s (%s)" % (course.name, team.id, student_names)
        github_instructors = self.__get_team_by_name(course.github_admins_team)
        
        github_repo = self.__get_repository(repo_name)
        
        if github_repo is None:
            try:
                github_repo = self.organization.create_repo(repo_name, description=repo_description, private=private)
            except GithubException as ge:
                raise ChisubmitException("Unexpected exception creating repository %s (%i: %s)" % (repo_name, ge.status, ge.data["message"]), ge)
        else:
            if fail_if_exists:
                raise ChisubmitException("Repository %s already exists" % repo_name)
        
        try:
            github_instructors.add_to_repos(github_repo)
        except GithubException as ge:
            raise ChisubmitException("Unexpected exception adding repository to Instructors team (%i: %s)" % (ge.status, ge.data["message"]), ge)
        
        team.github_repo = repo_name
        
        github_team = self.create_team(team_name, [github_repo], "push", fail_if_exists)
        
        team.github_team = team_name

        for s in team.students:
            github_student = self.__get_user(s.github_id)
            try:
                github_team.add_to_members(github_student)
            except GithubException as ge:
                raise ChisubmitException("Unexpected exception adding user %s to team (%i: %s)" % (s.github_id, ge.status, ge.data["message"]), ge)

    def update_team_repository(self, team):
        github_team = self.__get_team_by_name(team.github_team)

        for s in team.students:
            github_student = self.__get_user(s.github_id)
            try:
                github_team.add_to_members(github_student)
            except GithubException as ge:
                raise ChisubmitException("Unexpected exception adding user %s to team (%i: %s)" % (s.github_id, ge.status, ge.data["message"]))


    def create_team(self, team_name, repos, permissions, fail_if_exists = True):
        github_team = self.__get_team_by_name(team_name)
        
        if github_team is not None:
            if fail_if_exists:
                raise ChisubmitException("Team %s already exists." % team_name)
            else:
                return github_team
        else:
            try:
                github_team = self.organization.create_team(team_name, repos, permissions)
                return github_team
            except GithubException as ge:
                raise ChisubmitException("Unexpected exception creating team %s (%i: %s)" % (team_name, ge.status, ge.data["message"]), ge)


    def create_submission_tag(self, team, tag_name, tag_message, commit_sha):
        github_repo = self.organization.get_repo(team.github_repo)
        
        commit = self.get_commit(team, commit_sha)
        
        this_user = self.gh.get_user()
        tz = pytz.timezone("America/Chicago")
        dt = tz.localize(datetime.now())
        iu = InputGitAuthor(this_user.name, this_user.email, dt.isoformat())
        
        tag = github_repo.create_git_tag(tag_name, tag_message, commit.sha, "commit", iu)
        ref = github_repo.create_git_ref("refs/tags/" + tag.tag, tag.sha)
        
    def update_submission_tag(self, team, tag_name, tag_message, commit_sha):
        submission_tag_ref = self.get_submission_tag_ref(team, tag_name)
        submission_tag_ref.delete()
        
        self.create_submission_tag(team, tag_name, tag_message, commit_sha)
        
    def get_submission_tag_ref(self, team, tag_name):
        github_repo = self.organization.get_repo(team.github_repo)
        
        try:
            submission_tag_ref = github_repo.get_git_ref("tags/" + tag_name)
        except GithubException as ge:
            if ge.status == 404:
                return None
            else:
                raise ChisubmitException("Unexpected error when fetching tag %s (%i: %s)" % (tag_name, ge.status, ge.data["message"]), ge)            
        
        return submission_tag_ref

            
    def get_submission_tag(self, team, tag_name):
        github_repo = self.organization.get_repo(team.github_repo)
        
        submission_tag_ref = self.get_submission_tag_ref(team, tag_name)
        
        if submission_tag_ref is None:
            return None
                
        submission_tag = github_repo.get_git_tag(submission_tag_ref.object.sha)
        
        return submission_tag  

    def delete_team_repository(self, team):
        try:
            github_repo = self.organization.get_repo(team.github_repo)
        except GithubException as ge:
            raise ChisubmitException("Unexpected exception fetching repository %s (%i: %s)" % (team.github_repo, ge.status, ge.data["message"]), ge)
        
        try:
            github_repo.delete()
        except GithubException as ge:
            raise ChisubmitException("Unexpected exception deleting repository %s (%i: %s)" % (team.github_repo, ge.status, ge.data["message"]), ge)
        
        team.github_repo = None
        
        github_team = self.__get_team_by_name(team.github_team)

        try:
            github_team.delete()
        except GithubException as ge:
            raise ChisubmitException("Unexpected exception deleting team %s (%i: %s)" % (team.github_team, ge.status, ge.data["message"]), ge)

        team.github_team = None

    def get_commit(self, team, commit_sha):
        try:
            github_repo = self.organization.get_repo(team.github_repo)
            commit = github_repo.get_commit(commit_sha)
            return commit
        except GithubException as ge:
            if ge.status == 404:
                return None
            else:
                raise ChisubmitException("Unexpected error when fetching commit %s (%i: %s)" % (commit_sha, ge.status, ge.data["message"]), ge)            


    def __get_user(self, username):
        try:
            user = self.gh.get_user(username)
            return user
        except GithubException as ge:
            if ge.status == 404:
                return None
            else:
                raise ChisubmitException("Unexpected error with user %s (%i: %s)" % (username, ge.status, ge.data["message"]), ge)            


    def __get_repository(self, repository_name):
        try:
            repository = self.organization.get_repo(repository_name)
            return repository
        except GithubException as ge:
            if ge.status == 404:
                return None
            else:
                raise ChisubmitException("Unexpected error with repository %s (%i: %s)" % (repository_name, ge.status, ge.data["message"]), ge)            


    def __get_team_by_name(self, team_name):
        try:
            teams = self.organization.get_teams()
            for t in teams:
                if t.name == team_name:
                    return t
            return None
        except GithubException as ge:
            raise ChisubmitException("Unexpected error with team %s (%i: %s)" % (team_name, ge.status, ge.data["message"]), ge)
        
        
class LocalGitRepo(object):
    def __init__(self, directory):
        self.repo = git.Repo(directory)
        
        rems = [rem for rem in self.repo.remotes if rem.url.startswith("git@github.com")]
        
        if len(rems) == 0:
            self.gh_remote = None
        elif len(rems) == 1:
            self.gh_remote = rems[0]
        else:
            raise ChisubmitException("Repository at %s has more than one GitHub remote" % directory)        

        rems = [rem for rem in self.repo.remotes if not rem.url.startswith("git@github.com")]
        
        if len(rems) == 0:
            self.priv_remote = None
        elif len(rems) == 1:
            self.priv_remote = rems[0]
        else:
            raise ChisubmitException("Repository at %s has more than one non-GitHub remote" % directory)        


    def fetch(self):
        self.gh_remote.fetch()

    def reset_branch(self, branch):
        branch_refpath = "refs/heads/%s" % branch
        remote_branch_refpath = "refs/remotes/%s/%s" % (self.gh_remote.name, branch)
        
        branch_head = self.__get_head(branch_refpath)
        remote_branch = self.__get_ref(remote_branch_refpath)
        
        if branch_head is None:
            raise ChisubmitException("No such branch: %s" % branch)

        if remote_branch is None:
            raise ChisubmitException("No such remote branch: %s" % branch)

        if self.repo.head.ref != branch_head:
            try:
                branch_head.checkout()
            except GitCommandError, gce:
                print gce
                raise ChisubmitException("Error checking out")
        
        self.repo.head.reset(remote_branch.commit, index=True, working_tree=True)

    def has_branch(self, branch):
        return (self.__get_branch(branch) is not None)
    
    def push_branch_to_github(self, branch):
        self.__push(self.gh_remote, branch)

    def push_branch_to_staging(self, branch):
        self.__push(self.priv_remote, branch)

    def pull_branch_from_github(self, branch):
        self.__pull(self.gh_remote, branch)

    def pull_branch_from_staging(self, branch):
        self.__pull(self.priv_remote, branch)

    
    def checkout_branch(self, branch):
        branch_refpath = "refs/heads/%s" % branch
        branch_head = self.__get_head(branch_refpath)
            
        if branch_head is None:
            raise ChisubmitException("No such branch: %s" % branch)    
        
        try:
            branch_head.checkout()
        except GitCommandError, gce:
            raise ChisubmitException("Error checking out")                

    def get_tag(self, tag):
        tags = [t for t in self.repo.tags if t.name == tag]
        
        if len(tags) == 0:
            return None
        else:
            return tags[0]           

    def has_tag(self, tag):
        return (self.get_tag(tag) is not None)
    
    def create_branch(self, branch, commit):
        self.repo.create_head(branch, commit)

    @staticmethod
    def get_team_local_repo_path(course, team):
        return "%s/repositories/%s/%s" % (chisubmit.core.chisubmit_dir, course.id, team.id)
    
    @classmethod
    def get_team_local_repo(cls, course, team):
        repo_path = cls.get_team_local_repo_path(course, team)
        if not os.path.exists(repo_path):
            return None 
        else:
            return cls(repo_path)
    
    @classmethod
    def create_team_local_repo(cls, course, team):
        repo_path = cls.get_team_local_repo_path(course, team)
        gh_url = course.get_team_gh_repo_url(team.id)
        priv_url = course.get_team_staging_repo_url(team.id)
        return cls.create_repo(repo_path, gh_url, priv_url)        
    
    @classmethod
    def create_repo(cls, directory, gh_remote = None, priv_remote = None):
        if gh_remote is None:
            pass
        else:
            repo = git.Repo.clone_from(gh_remote, directory)
            
            if priv_remote is not None:
                repo.create_remote('staging', priv_remote)
            
            return cls(directory)

    def __get_head(self, path):
        heads = [h for h in self.repo.heads if h.path == path]
        
        if len(heads) == 0:
            return None
        else:
            return heads[0]

    def __get_branch(self, branch):
        branches = [b for b in self.repo.branches if b.name == branch]
        
        if len(branches) == 0:
            return None
        else:
            return branches[0]   
            
    def __get_ref(self, path):
        refs = [r for r in self.repo.refs if r.path == path]
        
        if len(refs) == 0:
            return None
        else:
            return refs[0]    
                    
    def __push(self, remote, branch):
        remote.push("%s:%s" % (branch, branch))

    def __pull(self, remote, branch):
        remote.pull("%s:%s" % (branch, branch))        
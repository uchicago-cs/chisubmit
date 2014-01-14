
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
        github_students = []
        
        # Make sure users exist
        for s in team.students:
            github_student = self.__get_user(s.github_id)
            
            if github_student is None:
                raise ChisubmitException("GitHub user '%s' does not exist " % (s.github_id))
            
            github_students.append(github_student)
        
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
        
        github_team = self.create_team(team_name, [github_repo], "push", fail_if_exists)
        
        for github_student in github_students:
            try:
                github_team.add_to_members(github_student)
            except GithubException as ge:
                raise ChisubmitException("Unexpected exception adding user %s to team (%i: %s)" % (s.github_id, ge.status, ge.data["message"]), ge)
            
        # Update team information only once everything has completed
        # successfully
        team.github_repo = repo_name
        team.github_team = team_name
            

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

        if this_user.name is None:
            user_name = "Team %s" % team.id
        else:
            user_name = this_user.name

        if this_user.email is None:
            user_email = "unspecified@example.org"
        else:
            user_email = this_user.email

        tz = pytz.timezone("America/Chicago")
        dt = tz.localize(datetime.now())
        iu = InputGitAuthor(user_name, user_email, dt.isoformat())
        
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


    def repository_exists(self, github_repo):
        r = self.__get_repository(github_repo)
        
        return (r is not None)
        

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
        
    @staticmethod
    def get_token(username, password, delete = False):
        gh = Github(username, password)
        token = None
        
        try:
            u = gh.get_user()
            
            scopes = ['user', 'public_repo', 'repo', 'gist']
            note = "Created by chisubmit."
            
            if delete:
                scopes.append("delete_repo")
                note += " Has delete permissions."
                
            auth = u.create_authorization(scopes = scopes, note = note)
            token = auth.token
        except GithubException as ge:
            if ge.status == 401:
                return None
            else:
                raise ChisubmitException("Unexpected error creating authorization token (%i: %s)" % (ge.status, ge.data["message"]), ge)            
        
        return token
    
class LocalGitRepo(object):
    def __init__(self, directory):
        self.repo = git.Repo(directory)
        
        self.remotes = dict([(r.name, r) for r in self.repo.remotes])

    @classmethod
    def create_repo(cls, directory, clone_from_url = None, remotes = []):
        if clone_from_url is None:
            # TODO: Create empty repo
            pass
        else:
            repo = git.Repo.clone_from(clone_from_url, directory)
            
            for remote_name, remote_url in remotes:
                repo.create_remote(remote_name, remote_url)
            
            return cls(directory)

    def fetch(self, remote_name):
        self.remotes[remote_name].fetch()

    def reset_branch(self, remote_name, branch):
        branch_refpath = "refs/heads/%s" % branch
        remote_branch_refpath = "refs/remotes/%s/%s" % (remote_name, branch)
        
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

    def push(self, remote_name, branch):
        self.remotes[remote_name].push("%s:%s" % (branch, branch))

    def pull(self, remote_name, branch):
        self.remotes[remote_name].pull("%s:%s" % (branch, branch))        


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
        
class GradingGitRepo(object):
    def __init__(self, team, repo):
        self.team = team        
        self.repo = repo
    
    @classmethod
    def get_grading_repo(cls, course, team):
        repo_path = cls.get_grading_repo_path(course, team)
        if not os.path.exists(repo_path):
            return None 
        else:
            repo = LocalGitRepo(repo_path)
            return cls(team, repo)
    
    @classmethod
    def create_grading_repo(cls, course, team):
        repo_path = cls.get_grading_repo_path(course, team)
        gh_url = cls.get_team_gh_repo_url(course, team)
        staging_url = cls.get_team_staging_repo_url(course, team)
        repo = LocalGitRepo.create_repo(repo_path, clone_from_url = gh_url, remotes = [("staging", staging_url)])
        return cls(team, repo)        
    
    def sync(self):
        self.repo.fetch("origin")
        self.repo.reset_branch("origin", "master")
        
    def create_grading_branch(self, project):
        tag = self.repo.get_tag(project.id)
        if tag is None:
            raise ChisubmitException("%s repository does not have a %s tag" % (self.team.id, project.id))
        
        branch_name = project.get_grading_branch_name()
        if self.repo.has_branch(branch_name):
            raise ChisubmitException("%s repository already has a %s branch" % (self.team.id, branch_name))
        
        self.repo.create_branch(branch_name, tag.commit)
        self.repo.checkout_branch(branch_name)
        
        
    def push_grading_branch_to_github(self, project):
        self.__push_grading_branch(project, "origin")

    def push_grading_branch_to_staging(self, project):
        self.__push_grading_branch(project, "staging", push_master = True)

    def pull_grading_branch_from_github(self, project):
        self.__pull_grading_branch(project, "origin")

    def pull_grading_branch_from_staging(self, project):
        self.__pull_grading_branch(project, "staging")

    def __push_grading_branch(self, project, remote_name, push_master = False):
        branch_name = project.get_grading_branch_name()
        
        if not self.repo.has_branch(branch_name):
            raise ChisubmitException("%s repository does not have a %s branch" % (self.team.id, branch_name))
        
        if push_master:
            self.repo.push(remote_name, "master")
            
        self.repo.push(remote_name, branch_name)
        
    def __pull_grading_branch(self, project, remote_name):
        branch_name = project.get_grading_branch_name()
        self.repo.pull(remote_name, branch_name)

    @staticmethod
    def get_grading_repo_path(course, team):
        return "%s/repositories/%s/%s" % (chisubmit.core.chisubmit_dir, course.id, team.id)
    
    @staticmethod
    def get_team_gh_repo_url(course, team):        
        return "git@github.com:%s/%s.git" % (course.github_organization, team.github_repo)       

    @staticmethod
    def get_team_staging_repo_url(course, team):
        if course.git_staging_hostname is None or course.git_staging_username is None:
            return None
        else:
            return "%s@%s:%s.git" % (course.git_staging_username, course.git_staging_hostname, team.github_repo)
                
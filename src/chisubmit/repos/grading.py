import git
import os.path

import chisubmit.core
from chisubmit.core import ChisubmitException
from git.exc import GitCommandError


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

    def fetch(self, remote_name, branch = None):
        if branch is None:
            self.remotes[remote_name].fetch()
        else:
            self.remotes[remote_name].fetch("%s:%s" % (branch, branch))

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

    def has_remote_branch(self, remote_name, branch):
        return (self.__get_ref("refs/remotes/%s/%s" % (remote_name, branch)) is not None)

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
        self.remotes[remote_name].pull("%s" % (branch))


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
    def __init__(self, team, project, repo, repo_path):
        self.team = team
        self.project = project
        self.repo = repo
        self.repo_path = repo_path

    @classmethod
    def get_grading_repo(cls, course, team, project):
        repo_path = cls.get_grading_repo_path(course, team, project)
        if not os.path.exists(repo_path):
            return None
        else:
            repo = LocalGitRepo(repo_path)
            return cls(team, project, repo, repo_path)

    @classmethod
    def create_grading_repo(cls, course, team, project):
        conn = course.get_git_server_connection()
        conn_staging = course.get_git_staging_server_connection()

        repo_path = cls.get_grading_repo_path(course, team, project)
        gh_url = conn.get_repository_git_url(course, team)
        staging_url = conn_staging.get_repository_git_url(course, team)

        repo = LocalGitRepo.create_repo(repo_path, clone_from_url = gh_url, remotes = [("staging", staging_url)])
        return cls(team, project, repo, repo_path)

    def sync(self):
        self.repo.fetch("origin")
        self.repo.fetch("staging")
        self.repo.reset_branch("origin", "master")

    def create_grading_branch(self):
        branch_name = self.project.get_grading_branch_name()
        if self.repo.has_branch(branch_name):
            raise ChisubmitException("%s repository already has a %s branch" % (self.team.id, branch_name))

        tag = self.repo.get_tag(self.project.id)
        if tag is None:
            self.sync()
            tag = self.repo.get_tag(self.project.id)
            if tag is None:
                raise ChisubmitException("%s repository does not have a %s tag" % (self.team.id, self.project.id))

        self.repo.create_branch(branch_name, tag.commit)
        self.repo.checkout_branch(branch_name)

    def has_grading_branch(self):
        branch_name = self.project.get_grading_branch_name()
        return self.repo.has_branch(branch_name)

    def has_grading_branch_staging(self):
        branch_name = self.project.get_grading_branch_name()
        return self.repo.has_remote_branch("staging", branch_name)

    def has_grading_branch_github(self):
        branch_name = self.project.get_grading_branch_name()
        return self.repo.has_remote_branch("origin", branch_name)

    def checkout_grading_branch(self):
        branch_name = self.project.get_grading_branch_name()
        if not self.repo.has_branch(branch_name):
            raise ChisubmitException("%s repository does not have a %s branch" % (self.team.id, branch_name))

        self.repo.checkout_branch(branch_name)

    def push_grading_branch_to_github(self):
        self.__push_grading_branch("origin")

    def push_grading_branch_to_staging(self):
        self.__push_grading_branch("staging", push_master = True)

    def pull_grading_branch_from_github(self):
        self.__pull_grading_branch("origin", pull_master = True)

    def pull_grading_branch_from_staging(self):
        self.__pull_grading_branch("staging")

    def set_grader_author(self):
        c = self.repo.repo.config_writer()

        c.set_value("user", "name", "chisubmit grader")
        c.set_value("user", "email", "do-not-email@example.org")

    def __push_grading_branch(self, remote_name, push_master = False):
        branch_name = self.project.get_grading_branch_name()

        if not self.repo.has_branch(branch_name):
            raise ChisubmitException("%s repository does not have a %s branch" % (self.team.id, branch_name))

        if push_master:
            self.repo.push(remote_name, "master")

        self.repo.push(remote_name, branch_name)

    def __pull_grading_branch(self, remote_name, pull_master = False):
        if pull_master:
            self.repo.checkout_branch("master")
            self.repo.pull(remote_name, "master")

        branch_name = self.project.get_grading_branch_name()
        if self.repo.has_branch(branch_name):
            self.repo.checkout_branch(branch_name)
            self.repo.pull(remote_name, branch_name)
        else:
            self.repo.fetch(remote_name, branch_name)
            self.repo.checkout_branch(branch_name)

    @staticmethod
    def get_grading_repo_path(course, team, project):
        return "%s/repositories/%s/%s/%s" % (chisubmit.core.chisubmit_dir, course.id, project.id, team.id)


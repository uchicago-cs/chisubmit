import os.path

from chisubmit.common import ChisubmitException
from chisubmit.repos.local import LocalGitRepo
from chisubmit.common.utils import create_connection


class GradingGitRepo(object):
    def __init__(self, team, registration, repo, repo_path, commit_sha):
        self.team = team
        self.registration = registration
        self.repo = repo
        self.repo_path = repo_path
        self.commit_sha = commit_sha

    @classmethod
    def get_grading_repo(cls, config, course, team, registration):
        base_dir = config.work_dir
                
        repo_path = cls.get_grading_repo_path(base_dir, course, team, registration)
        if not os.path.exists(repo_path):
            return None
        else:
            repo = LocalGitRepo(repo_path)
            if registration.final_submission is None:
                commit_sha = None
            else:
                commit_sha = registration.final_submission.commit_sha
            return cls(team, registration, repo, repo_path, commit_sha)

    @classmethod
    def create_grading_repo(cls, config, course, team, registration):
        base_dir = config.work_dir
        
        conn_server = create_connection(course, config)
        if conn_server is None:
            raise ChisubmitException("Could not connect to git server")
        
        conn_staging = create_connection(course, config, staging = True)
        if conn_server is None:
            raise ChisubmitException("Could not connect to git staging server")        
        
        repo_path = cls.get_grading_repo_path(base_dir, course, team, registration)
        server_url = conn_server.get_repository_git_url(course, team)
        staging_url = conn_staging.get_repository_git_url(course, team)

        repo = LocalGitRepo.create_repo(repo_path, clone_from_url = server_url, remotes = [("staging", staging_url)])
        if registration.final_submission is None:
            commit_sha = None
        else:
            commit_sha = registration.final_submission.commit_sha        
        return cls(team, registration, repo, repo_path, commit_sha)

    def sync(self):
        self.repo.fetch("origin")
        self.repo.fetch("staging")
        self.repo.reset_branch("origin", "master")

    def create_grading_branch(self):
        branch_name = self.registration.get_grading_branch_name()
        if self.repo.has_branch(branch_name):
            raise ChisubmitException("%s repository already has a %s branch" % (self.team.team_id, branch_name))

        if self.commit_sha is not None:
            commit = self.repo.get_commit(self.commit_sha)
            if commit is None:
                self.sync()
                commit = self.repo.get_commit(self.commit_sha)
                if commit is None:
                    raise ChisubmitException("%s repository does not have a commit %s" % (self.team.team_id, self.commit_sha))

            self.repo.create_branch(branch_name, self.commit_sha)
            self.repo.checkout_branch(branch_name)

    def has_grading_branch(self):
        branch_name = self.registration.get_grading_branch_name()
        return self.repo.has_branch(branch_name)

    def has_grading_branch_staging(self):
        branch_name = self.registration.get_grading_branch_name()
        return self.repo.has_remote_branch("staging", branch_name)

    def has_grading_branch_github(self):
        branch_name = self.registration.get_grading_branch_name()
        return self.repo.has_remote_branch("origin", branch_name)

    def checkout_grading_branch(self):
        branch_name = self.registration.get_grading_branch_name()
        if not self.repo.has_branch(branch_name):
            raise ChisubmitException("%s repository does not have a %s branch" % (self.team.team_id, branch_name))

        self.repo.checkout_branch(branch_name)

    def push_grading_branch_to_students(self):
        self.__push_grading_branch("origin")

    def push_grading_branch_to_staging(self):
        self.__push_grading_branch("staging", push_master = True)

    def pull_grading_branch_from_students(self):
        self.__pull_grading_branch("origin", pull_master = True)

    def pull_grading_branch_from_staging(self):
        self.__pull_grading_branch("staging")

    def set_grader_author(self):
        c = self.repo.repo.config_writer()

        c.set_value("user", "name", "chisubmit grader")
        c.set_value("user", "email", "do-not-email@example.org")

    def __push_grading_branch(self, remote_name, push_master = False):
        branch_name = self.registration.get_grading_branch_name()

        if not self.repo.has_branch(branch_name):
            raise ChisubmitException("%s repository does not have a %s branch" % (self.team.id, branch_name))

        if push_master:
            self.repo.push(remote_name, "master")

        self.repo.push(remote_name, branch_name)

    def __pull_grading_branch(self, remote_name, pull_master = False):
        if pull_master:
            self.repo.checkout_branch("master")
            self.repo.pull(remote_name, "master")

        branch_name = self.registration.get_grading_branch_name()
        if self.repo.has_branch(branch_name):
            self.repo.checkout_branch(branch_name)
            self.repo.pull(remote_name, branch_name)
        else:
            self.repo.fetch(remote_name, branch_name)
            self.repo.checkout_branch(branch_name)

    def commit(self, files, commit_message):
        return self.repo.commit(files, commit_message)

    def is_dirty(self):
        return self.repo.is_dirty()


    @staticmethod
    def get_grading_repo_path(base_dir, course, team, registration):
        # TODO 18DEC14: This code could be a problem
        # The base_dir is passed from far away
        return "%s/repositories/%s/%s/%s" % (base_dir, course.course_id, registration.assignment.assignment_id, team.team_id)
    
    

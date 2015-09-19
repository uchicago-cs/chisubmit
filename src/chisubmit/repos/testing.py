import git

from chisubmit.repos import RemoteRepositoryConnectionBase, GitCommit
from chisubmit.common import ChisubmitException
import os
from gitdb.exc import BadObject
import datetime
from chisubmit.repos.local import LocalGitRepo

class TestingConnection(RemoteRepositoryConnectionBase):

    VALID_CREDENTIALS = "testing-credentials"

    def __init__(self, connection_string, staging):
        RemoteRepositoryConnectionBase.__init__(self, connection_string, staging)
        
    @staticmethod
    def get_server_type_name():
        return "Testing"
    
    @staticmethod
    def get_connstr_mandatory_params():
        return ["local_path"]

    @staticmethod
    def get_connstr_optional_params():
        return []
    
    @staticmethod
    def supports_user_creation():
        return False    
    
    
    @staticmethod
    def get_credentials(username, password, delete_repo = False):
        return "testing-credentials"
    
    def connect(self, credentials):
        if credentials != self.VALID_CREDENTIALS:
            raise ChisubmitException("Invalid Testing Credentials")
    
    def disconnect(self, credentials):
        pass
    
    def init_course(self, course, fail_if_exists=True):
        pass            
    
    def deinit_course(self, course):
        pass
        
    def exists_user(self, course, course_user):
        pass

    def create_user(self, course, course_user):
        pass        
        
    def update_instructors(self, course):
        pass

    def update_graders(self, course):
        pass

    def create_team_repository(self, course, team, fail_if_exists=True, private=True):
        repo_path = self.__get_team_path(course, team)
        
        if os.path.exists(repo_path) and fail_if_exists:
            raise ChisubmitException("Repository %s already exists" % repo_path)
        
        repo = LocalGitRepo.create_repo(repo_path, bare=True)
        
    def update_team_repository(self, course, team):
        pass
    
    def exists_team_repository(self, course, team):
        repo_path = self.__get_team_path(course, team)
        
        return os.path.exists(repo_path)
    
    def get_repository_git_url(self, course, team):
        repo_path = self.__get_team_path(course, team)
        return repo_path
            
    def get_repository_http_url(self, course, team):
        return None
    
    def get_commit(self, course, team, commit_sha):
        repo_path = self.__get_team_path(course, team)
        repo = LocalGitRepo(repo_path)
        
        return repo.get_commit(commit_sha)        
        
    
    def create_submission_tag(self, course, team, tag_name, tag_message, commit_sha):
        repo_path = self.__get_team_path(course, team)
        repo = LocalGitRepo(repo_path)
        
        tag = repo.create_tag(tag_name, commit_sha, tag_message)
    
    def update_submission_tag(self, course, team, tag_name, tag_message, commit_sha):
        repo_path = self.__get_team_path(course, team)
        repo = LocalGitRepo(repo_path)
                
        tag = repo.create_tag(tag_name, commit_sha, tag_message, force=True)
            
    def get_submission_tag(self, course, team, tag_name):
        repo_path = self.__get_team_path(course, team)
        repo = LocalGitRepo(repo_path)
        
        tag = repo.get_tag(tag_name)
        
        if tag is None:
            return None
        else:
            return tag
    
    def delete_team_repository(self, course, team, fail_if_not_exists=True):
        pass
    
    def __get_team_path(self, course, team):
        return "%s/%s/%s.git" % (os.path.abspath(self.local_path), course.course_id, team.team_id)   
        

import git

from chisubmit.repos import RemoteRepositoryConnectionBase
from chisubmit.common import ChisubmitException
import os

class TestingConnection(RemoteRepositoryConnectionBase):

    VALID_CREDENTIALS = "testing-credentials"

    def __init__(self, connection_string):
        RemoteRepositoryConnectionBase.__init__(self, connection_string)   
        
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
    def get_credentials(username, password, delete_repo = False):
        return "testing-credentials"
    
    def connect(self, credentials):
        if credentials != self.VALID_CREDENTIALS:
            raise ChisubmitException("Invalid Testing Credentials")
    
    def disconnect(self, credentials):
        pass
    
    def init_course(self, course, fail_if_exists=True):
        pass            
    
    def update_instructors(self, course):
        pass

    def update_graders(self, course):
        pass

    def create_team_repository(self, course, team, team_access, fail_if_exists=True, private=True):
        repo_path = self.__get_team_path(course, team)
        
        if os.path.exists(repo_path) and fail_if_exists:
            raise ChisubmitException("Repository %s already exists" % repo_path)
        
        os.makedirs(repo_path)
        
        repo = git.Repo.init(repo_path, bare=True)
    
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
        pass
    
    def create_submission_tag(self, course, team, tag_name, tag_message, commit_sha):
        pass
    
    def update_submission_tag(self, course, team, tag_name, tag_message, commit_sha):
        pass
    
    def get_submission_tag(self, course, team, tag_name):
        pass
    
    def delete_team_repository(self, course, team):
        pass
    
    def __get_team_path(self, course, team):
        return "%s/%s/%s" % (self.local_path, course.id, team.id)   
        
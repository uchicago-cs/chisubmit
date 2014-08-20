from gitlab import Gitlab

from chisubmit.repos import RemoteRepositoryConnectionBase
from chisubmit.core import ChisubmitException
import pytz
from datetime import datetime

class GitLabConnection(RemoteRepositoryConnectionBase):

    def __init__(self, connection_string):
        RemoteRepositoryConnectionBase.__init__(self, connection_string)   
        
    @staticmethod
    def get_server_type_name():
        return "GitLab"
    
    @staticmethod
    def get_connstr_mandatory_params():
        return ["gitlab_hostname"]

    @staticmethod
    def get_connstr_optional_params():
        return []
    
    @staticmethod
    def get_credentials(username, password, delete_repo = False):
        pass
    
    def connect(self, credentials):
        # Credentials are a GitLab private token
        self.gitlab = Gitlab(self.gitlab_hostname, token=credentials)    
        try:
            # Test connection by grabbing current user
            user = self.gitlab.currentuser()
            
            if user.has_key("message") and user["message"] == "401 Unauthorized":
                raise ChisubmitException("Invalid GitLab credentials for server '%s': %s" % (self.gitlab_hostname))
            
            if not user.has_key("username"):
                raise ChisubmitException("Unexpected error connecting to GitLab server '%s': %s" % (self.gitlab_hostname))
                
        except Exception as e:
            raise ChisubmitException("Unexpected error connecting to GitLab server '%s': %s" % (self.gitlab_hostname, e.message))       

    def disconnect(self, credentials):
        pass
    
    def init_course(self, course):
        pass
    
    def update_instructors(self, course):
        pass
    
    def update_graders(self, course):
        pass
    
    def create_team_repository(self, course, team, team_access, fail_if_exists=True, private=True):
        pass
    
    def update_team_repository(self, course, team):
        pass
    
    def exists_team_repository(self, course, team):
        pass
    
    def get_repository_git_url(self, course, team):
        pass
    
    def get_repository_http_url(self, course, team):
        pass
    
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
        
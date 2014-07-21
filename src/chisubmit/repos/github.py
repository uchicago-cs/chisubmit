
# Needed so we can import from the global "github" package
from __future__ import absolute_import

from github import Github
from github.GithubException import GithubException

import chisubmit.core
from chisubmit.repos import RemoteRepositoryConnectionBase
from chisubmit.core import ChisubmitException

class GitHubConnection(RemoteRepositoryConnectionBase):

    def __init__(self, connection_string):
        RemoteRepositoryConnectionBase.__init__(self, connection_string)   
        
        self.organization = None   
        self.gh = None  

    @staticmethod
    def get_server_type_name():
        return "GitHub"
    
    @staticmethod
    def get_connstr_mandatory_params():
        return ["github_organization"]

    @staticmethod
    def get_connstr_optional_params():
        return []

    def connect(self):
        github_access_token = chisubmit.core.get_github_token()

        if github_access_token is None:
            raise ChisubmitException("Not GitHub access token found.")
        
        self.gh = Github(github_access_token)
        
        try:
            self.organization = self.gh.get_organization(self.github_organization)
        except GithubException as ge:
            if ge.status == 401:
                raise ChisubmitException("Invalid Github Credentials", ge)
            elif ge.status == 404:
                raise ChisubmitException("Organization %s does not exist" % self.github_organization, ge)            
            else:
                raise ChisubmitException("Unexpected error accessing organization %s (%i: %s)" % (self.github_organization, ge.status, ge.data["message"]), ge)            
        

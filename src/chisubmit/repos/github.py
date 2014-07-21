from chisubmit.repos import RemoteRepositoryConnectionBase

class GitHubConnection(RemoteRepositoryConnectionBase):

    def __init__(self, connection_string):
        RemoteRepositoryConnectionBase.__init__(self, connection_string)        

    @staticmethod
    def get_server_type_name():
        return "GitHub"
    
    @staticmethod
    def get_connstr_mandatory_params():
        return ["organization"]

    @staticmethod
    def get_connstr_optional_params():
        return []


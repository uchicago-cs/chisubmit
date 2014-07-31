from chisubmit.repos import ConnectionString
from chisubmit.core import ChisubmitException
from chisubmit.repos.github import GitHubConnection


class RemoteRepositoryConnectionFactory(object):
    
    server_types = {}
    
    @staticmethod
    def register_server_type(name, conn_cls):
        RemoteRepositoryConnectionFactory.server_types[name] = conn_cls
    
    @staticmethod
    def create_connection(connection_string):
        cs = ConnectionString(connection_string)
                
        if not RemoteRepositoryConnectionFactory.server_types.has_key(cs.server_type):
            raise ChisubmitException("Unsupported server type in connection string: %s (expected one of: %s)" % 
                                     (cs.server_type, ", ".join(RemoteRepositoryConnectionFactory.server_types.keys())))
        
        conn_cls = RemoteRepositoryConnectionFactory.server_types[cs.server_type]

        return conn_cls(cs)       
    
RemoteRepositoryConnectionFactory.register_server_type("GitHub", GitHubConnection)
from chisubmit.repos import ConnectionString
from chisubmit.common import ChisubmitException
from chisubmit.repos.github import GitHubConnection
from chisubmit.repos.gitlab import GitLabConnection
from chisubmit.repos.testing import TestingConnection


class RemoteRepositoryConnectionFactory(object):

    server_types = {}

    @staticmethod
    def register_server_type(name, conn_cls):
        RemoteRepositoryConnectionFactory.server_types[name] = conn_cls

    @staticmethod
    def create_connection(connection_string, staging):
        cs = ConnectionString(connection_string)

        if not RemoteRepositoryConnectionFactory.server_types.has_key(cs.server_type):
            raise ChisubmitException("Unsupported server type in connection string: %s (expected one of: %s)" %
                                     (cs.server_type, ", ".join(RemoteRepositoryConnectionFactory.server_types.keys())))

        conn_cls = RemoteRepositoryConnectionFactory.server_types[cs.server_type]

        return conn_cls(cs, staging)

RemoteRepositoryConnectionFactory.register_server_type("GitHub", GitHubConnection)
RemoteRepositoryConnectionFactory.register_server_type("GitLab", GitLabConnection)
RemoteRepositoryConnectionFactory.register_server_type("Testing", TestingConnection)

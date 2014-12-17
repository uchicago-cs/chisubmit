import abc
from chisubmit.core import ChisubmitException

class ConnectionString(object):

    def __init__(self, s):
        params = s.split(";")
        params = [x.split("=") for x in params]

        try:
            params = dict([(k.strip(), v.strip()) for k,v in params])
        except ValueError, ve:
            raise ChisubmitException("Improperly formatted connection string: %s" % s, original_exception = ve)

        if not params.has_key("server_type"):
            raise ChisubmitException("Connection string does not have 'server_type' parameter: %s" % s)

        self.server_type = params.pop("server_type")
        self.params = params

    @abc.abstractmethod
    def to_string(self):
        pass


class RemoteRepositoryConnectionBase(object):

    def __init__(self, connection_string):
        if connection_string.server_type != self.get_server_type_name():
            raise ChisubmitException("Expected server_type in connection string to be '%s', got '%s'" %
                                     (self.get_server_type_name(), connection_string.server_type))

        param_names = connection_string.params.keys()

        for p in self.get_connstr_mandatory_params():
            if p not in param_names:
                raise ChisubmitException("Connection string does not have required parameter '%s'" % p)
            param_names.remove(p)
            setattr(self, p, connection_string.params[p])

        for p in param_names:
            if p not in self.get_connstr_optional_params():
                raise ChisubmitException("Connection string has invalid parameter '%s'" % p)
            setattr(self, p, connection_string.params[p])

        for p in self.get_connstr_optional_params():
            if p not in param_names:
                setattr(self, p, None)


        self.is_connected = False

    @staticmethod
    @abc.abstractmethod
    def get_server_type_name():
        pass

    @staticmethod
    @abc.abstractmethod
    def get_connstr_mandatory_params():
        pass

    @staticmethod
    @abc.abstractmethod
    def get_connstr_optional_params():
        pass


    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass


class ChisubmitRequestException(Exception):

    def __init__(self, status, reason, data):
        Exception.__init__(self)
        self.__status = status
        self.__reason = reason
        self.__data = data

    @property
    def status(self):
        return self.__status

    @property
    def reason(self):
        return self.__reason

    @property
    def data(self):
        return self.__data

    def __str__(self):
        return str(self.status) + " " + self.reason + " " + self.data.get("detail", str(self.data))
    
    
class UnknownObjectException(ChisubmitRequestException):
    pass   
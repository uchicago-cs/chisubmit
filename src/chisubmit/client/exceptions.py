from pprint import pprint

class ChisubmitRequestException(Exception):

    def __init__(self, method, url, params, data, headers, response):
        Exception.__init__(self)
        self.__method = method
        self.__url = url
        self.__params = params
        self.__data = data
        self.__headers = headers
        self.__response = response

    @property
    def method(self):
        return self.__method

    @property
    def url(self):
        return self.__url
    
    @property
    def headers(self):
        return self.__headers    
    
    @property
    def params(self):
        return self.__params    
    
    @property
    def request_data(self):
        return self.__data    

    @property
    def status(self):
        return self.__response.status_code

    @property
    def reason(self):
        return self.__response.reason

    @property
    def json(self):    
        try:
            return self.__response.json()
        except ValueError:
            return {"data": self.__response.text}  

    @property
    def response_data(self):
        return self.__response.text

    def __str__(self):
        return "HTTP %i %s (%s %s)" % (self.status, self.reason, self.method, self.url)
    
    def print_debug_info(self):
        print "HTTP REQUEST"
        print "============"
        print "%s %s" % (self.method, self.url)
        print
        print "Headers"
        print "-------"
        for hname, hvalue in self.headers.items():
            print "%s: %s" % (hname, hvalue) 
        print
        print "Query string (GET parameters)"
        print "-----------------------------"
        if self.params is None:
            print "No querystring parameters"
        else:
            for pname, pvalue in self.params.items():
                print "%s: %s" % (pname, pvalue) 
        print
        print "Request data"
        print "------------"
        if self.request_data is None:
            print "No data included in request"
        else:
            pprint(self.request_data)
        print        
        print "HTTP RESPONSE"
        print "============="
        print "%s %s" % (self.status, self.reason)
        print
        print "Headers"
        print "-------"
        for hname, hvalue in self.__response.headers.items():
            print "%s: %s" % (hname, hvalue) 
        print
        print "Response body"
        print "-------------"        
        try:
            response_data = self.__response.json()
            pprint(response_data)
        except ValueError:
            response_data = self.__response.text
            print response_data
    
    
class UnauthorizedException(ChisubmitRequestException):
    def __init__(self, *args, **kwargs):
        super(UnauthorizedException, self).__init__(*args, **kwargs) 
    
    
class UnknownObjectException(ChisubmitRequestException):
    def __init__(self, *args, **kwargs):
        super(UnknownObjectException, self).__init__(*args, **kwargs) 


class BadRequestException(ChisubmitRequestException):
    
    def __init__(self, *args, **kwargs):
        super(BadRequestException, self).__init__(*args, **kwargs)
        
        try:
            self.errors = self.json
            if any([not isinstance(k, (str, unicode)) for k in self.errors.keys()]):
                raise ValueError
            if any([not isinstance(v, (list, tuple)) for v in self.errors.values()]):
                raise ValueError
            self.valid_errors = True        
        except ValueError:
            self.errors = {}
            self.valid_errors = False
              
    def print_errors(self):
        if self.valid_errors:
            for origin, reasons in self.errors.items():
                print origin
                for r in reasons:
                    print " - %s" % r
                print
        else:
            print "HTTP 400 response included incorrectly formatted error data:"
            print self.response_data
            

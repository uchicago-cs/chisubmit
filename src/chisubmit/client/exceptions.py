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
    def data(self):
        return self.__data

    def __str__(self):
        return str(self.status) + " " + self.reason + " " + self.data.get("detail", str(self.data))
    
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
        
    
    
class UnknownObjectException(ChisubmitRequestException):
    def __init__(self, *args, **kwargs):
        super(UnknownObjectException, self).__init__(*args, **kwargs) 


class BadRequestException(ChisubmitRequestException):
    
    def __init__(self, *args, **kwargs):
        #TODO: Initialize errors
        
        super(BadRequestException, self).__init__(*args, **kwargs)
        
    def print_errors(self):
        print "HTTP request %s %s returned error code 400 (Bad Request)" % (self.method, self.url)
        if len(self.errors) == 0:
            print "No additional error messages returned."
        else:
            for noun, message in self.errors:
                print "%s: %s" % (noun, message)
    

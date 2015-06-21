from enum import Enum

class ChisubmitAPIException(Exception):

    def __init__(self, status, data):
        Exception.__init__(self)
        self.__status = status
        self.__data = data

    @property
    def status(self):
        return self.__status

    @property
    def data(self):
        return self.__data

    def __str__(self):
        return str(self.status) + " " + str(self.data)


class AttributeType(Enum):
    STRING = 1,
    INTEGER = 2,
    BOOLEAN = 3,
    OBJECT = 4,
    LIST = 5,
    DICT = 6

class AttributeValidationException(Exception):
    
    def __init__(self, name, value, expected_type):
        self.name = name
        self.value = value
        self.expected_type = expected_type
        

class Attribute(object):
    
    def __init__(self, name, attrtype, patchable, items_type = None):
        if attrtype in (AttributeType.LIST, AttributeType.DICT):
            assert isinstance(items_type, AttributeType)
        else:
            assert items_type is None
        
        self.name = name
        self.type = attrtype
        self.patchable = patchable
        self.items_type = items_type
        
    @staticmethod
    def __validate(value, expected_type, items_type = None):
        valid = False
        if expected_type == AttributeType.STRING:
            valid = isinstance(value, basestring)
        elif expected_type == AttributeType.INTEGER:
            valid = isinstance(value, (int, long))
        elif expected_type == AttributeType.DICT:
            valid = isinstance(value, dict)
            valid &= all(isinstance(k, basestring) and Attribute.__validate(v, items_type) for k, v in value.iteritems())

        return valid
        
        
    def validate(self, value, raise_on_fail = True):
        valid = Attribute.__validate(value, self.type, self.items_type)
            
        if not valid and raise_on_fail:
            raise AttributeValidationException(self.name, value, self.type)
        else:
            return valid


class ChisubmitAPIObject(object):
    
    def __init__(self, requester, headers, attributes):
        self._requester = requester
        self._headers = headers
        self._rawData = attributes
        self._attrtypes = self.__getattrtypes()
        self._updateAttributes(attributes)

    @property
    def raw_data(self):
        """
        :type: dict
        """
        return self._rawData

    @property
    def raw_headers(self):
        """
        :type: dict
        """
        return self._headers

    @staticmethod
    def _parentUrl(url):
        return "/".join(url.split("/")[: -1])

    def __getattrtypes(self):
        attrtypes = {}
        for attrname, attrvalue in self.__class__.__dict__.items():
            if isinstance(attrvalue, Attribute):
                attrtypes[attrname] = attrvalue
        return attrtypes

    def __getattrtype(self, attrname):
        attr = self.__class__.__dict__.get(attrname)
        if not isinstance(attr, Attribute):
            return None
        else:
            return attr
        
    def _initAttributes(self):
        for attr in self.__getattrtypes.values():
            setattr(self, attr.name, None)

    def _updateAttributes(self, attributes):
        
        for attrname, attrvalue in attributes.items():
            attrtype = self.__getattrtype(attrname)
            
            if attrtype is not None:
                attrtype.validate(attrvalue)
                
                setattr(self, attrname, attrvalue)
                
        

    def edit(self, **kwargs):
        
        request_parameters = {}

        headers, data = self._requester.request(
            "PATCH",
            self.url,
            input=request_parameters
        )
        self._updateAttributes(data)
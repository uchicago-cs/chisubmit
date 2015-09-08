import datetime
import pytz

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

class AttributeTypeException(Exception):
    
    def __init__(self, value, expected_type):
        self.value = value
        self.expected_type = expected_type


class AttributeException(Exception):
    
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "%s = %s" % (self.name, self.value)

class NoSuchAttributeException(AttributeException):
    pass

class AttributeNotEditableException(AttributeException):
    pass

class AttributeValidationException(AttributeException):
    
    def __init__(self, name, value, expected_type):
        AttributeException.__init__(self, name, value)
        self.expected_type = expected_type


class AttributeType(object):
    STRING = 1
    INTEGER = 2
    DECIMAL = 3
    DATETIME = 4
    BOOLEAN = 5
    OBJECT = 6
    LIST = 7
    DICT = 8
        
    primitive_types = [STRING, INTEGER, DECIMAL, DATETIME, BOOLEAN]
    composite_types = [OBJECT, LIST, DICT]
    
    def __init__(self, attrtype, subtype = None):
        assert((attrtype in self.primitive_types and subtype is None) or 
               (attrtype in self.composite_types and subtype is not None))
        
        assert(subtype is None or 
               (attrtype == self.LIST and isinstance(subtype, AttributeType)) or
               (attrtype == self.DICT and isinstance(subtype, AttributeType)) or
               (attrtype == self.OBJECT and isinstance(subtype, basestring)) or 
               (attrtype == self.OBJECT and issubclass(subtype, ChisubmitAPIObject)))
               
        # Based on http://stackoverflow.com/questions/547829/how-to-dynamically-load-a-python-class
        if attrtype == self.OBJECT and isinstance(subtype, basestring):
            subtypel = subtype.split(".")
            mod = __import__(".".join(subtypel[:-1]), fromlist=subtypel[-1])
            klass = getattr(mod, subtypel[-1])
            assert issubclass(klass, ChisubmitAPIObject)
            subtype = klass
            
        self.attrtype = attrtype
        self.subtype = subtype
        
    def to_python(self, value, headers, api_client):
        if self.attrtype == AttributeType.STRING:
            if not isinstance(value, basestring):
                raise AttributeTypeException(value, self)
            return value
        elif self.attrtype == AttributeType.INTEGER:
            if not isinstance(value, (int, long)):
                raise AttributeTypeException(value, self)
            return value
        elif self.attrtype == AttributeType.DECIMAL:
            try:
                return float(value)
            except ValueError:
                raise AttributeTypeException(value, self)
        elif self.attrtype == AttributeType.BOOLEAN:
            if not isinstance(value, bool):
                raise AttributeTypeException(value, self)
            return value
        elif self.attrtype == AttributeType.DATETIME:
            if not isinstance(value, basestring):
                raise AttributeTypeException(value, self)
            try:
                if value[19] == ".":
                    dt = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
                else:
                    dt = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
                dt = pytz.utc.localize(dt)
            except ValueError, ve:
                raise AttributeTypeException(value, self)
                
            return dt        
        elif self.attrtype == AttributeType.LIST:
            if not isinstance(value, (list, tuple)):
                raise AttributeTypeException(value, self)
            rvalue = []
            for item in value:
                rvalue.append(self.subtype.to_python(item, headers, api_client))
            return rvalue
        elif self.attrtype == AttributeType.DICT:
            if not isinstance(value, dict):
                raise AttributeTypeException(value, self)
            rvalue = {}
            for k, item in value.items():
                rvalue[k] = self.subtype.to_python(item, headers, api_client)
            return rvalue
        elif self.attrtype == AttributeType.OBJECT:
            if not isinstance(value, dict):
                raise AttributeTypeException(value, self)
            rvalue = self.subtype(api_client, headers, value)
            return rvalue
                
        raise AttributeTypeException(value, self)
    
    def to_json(self, value):
        # TODO
        pass

APIStringType = AttributeType(AttributeType.STRING)
APIIntegerType = AttributeType(AttributeType.INTEGER)
APIDecimalType = AttributeType(AttributeType.DECIMAL)
APIDateTimeType = AttributeType(AttributeType.DATETIME)
APIBooleanType = AttributeType(AttributeType.BOOLEAN)

def APIListType(subtype):
    return AttributeType(AttributeType.LIST, subtype)

def APIDictType(subtype):
    return AttributeType(AttributeType.DICT, subtype)

def APIObjectType(subtype):
    return AttributeType(AttributeType.OBJECT, subtype)
        

class Attribute(object):
    
    def __init__(self, name, attrtype, editable):        
        self.name = name
        self.type = attrtype
        self.editable = editable
        
    def to_python(self, value, headers, api_client):
        return self.type.to_python(value, headers, api_client)
    
    def to_json(self, value):
        return self.type.to_json(value)    


class ChisubmitAPIObject(object):
        
    def __init__(self, api_client, headers, attributes):
        self._api_client = api_client
        self._headers = headers
        self._rawData = attributes
        
        if self._api_client._deferred_save:
            self.dirty = {api_attr: False for api_attr in self._api_attributes}

        self._initAttributes()
        self._updateAttributes(attributes)

    def __has_api_attr(self, attrname):
        return self._api_attributes.has_key(attrname)

    def __get_api_attr(self, attrname):
        return self._api_attributes.get(attrname)
        
    def _initAttributes(self):
        for api_attr in self._api_attributes.keys():
            object.__setattr__(self, api_attr, None)

    def _updateAttributes(self, attributes):
        for attrname, attrvalue in attributes.items():
            api_attr = self.__get_api_attr(attrname)

            if api_attr is None:
                raise NoSuchAttributeException(attrname, attrvalue)
            else:
                if attrvalue is None:
                    checked_value = None
                else:
                    checked_value = api_attr.to_python(attrvalue, self._headers, self._api_client)
                object.__setattr__(self, attrname, checked_value)       

    def __setattr__(self, name, value):
        api_attr = self.__get_api_attr(name)
        if api_attr is None:        
            object.__setattr__(self, name, value)
        else:
            if not api_attr.editable:
                raise AttributeNotEditableException(name, value)
            else:
                if self._api_client._deferred_save:
                    self.dirty[name] = True
                else:
                    self.edit(**{name: value})                
                object.__setattr__(self, name, value)
                    
    def save(self):
        if self._api_client._deferred_save:
            attrs = {}
            for attrname, dirty in self.dirty.items():
                if dirty:
                    attrs[attrname] = getattr(self, attrname)
                    self.dirty[attrname] = False
            if len(attrs) > 0:
                self.edit(**attrs)            
        else:
            # TODO: Log a warning?
            pass

    def edit(self, **kwargs):
        patch_data = {}
        
        for attrname, attrvalue in kwargs.items():
            api_attr = self.__get_api_attr(attrname)
            
            if api_attr is None:
                raise NoSuchAttributeException(attrname, attrvalue)
            else:
                #value = api_attr.to_json(attrvalue)
                patch_data[attrname] = attrvalue

        headers, data = self._api_client._requester.request(
            "PATCH",
            self.url,
            data=patch_data
        )
        self._updateAttributes(data)
        
    def delete(self):
        """
        :calls: DELETE :url
        :rtype: None
        """
        
        _ = self._api_client._requester.request(
            "DELETE",
            self.url 
        )
        return None           
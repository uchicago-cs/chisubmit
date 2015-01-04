#  Copyright (c) 2013-2014, The University of Chicago
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  - Neither the name of The University of Chicago nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
import re
import json
from chisubmit.client import session
from datetime import datetime
import sys
from requests.exceptions import HTTPError

def json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()


class AttrOverride(type):

    def __getattr__(self, name):
        if name == 'singularize':
            return re.sub('(?!^)([A-Z]+)', r'_\1', self.__class__.__name__).lower()
        if name == 'pluralize':
            return self.singularize + 's'
        elif name == 'identifier':
            return self.__class__.__name__.lower() + '_id'
        else:
            raise AttributeError()

    def __new__(meta_class, name, bases, classdict):
        new_cls = type.__new__(meta_class, name, bases, classdict)
        for b in bases:
            if hasattr(b, 'register_subclass'):
                b.register_subclass(new_cls)
        return new_cls


class JSONObject(object):

    __metaclass__ = AttrOverride
    _subclasses = []

    def __init__(self, *args, **kwargs):
        class_id = self.__class__.__name__.lower() + '_id'
        for attr in self._api_attrs:
            if attr not in kwargs:
                kwargs[attr] = None
                
            super(JSONObject, self).__setattr__(attr, kwargs[attr])
                
            # FIXME 16JULY14: "alias" the id attribute.
            if attr == class_id:
                super(JSONObject, self).__setattr__("id", kwargs[attr])
        

    def __getattr__(self, name):
        class_attrs = self.__class__.__dict__

        if name == 'singularize':
            if '_singularize' in class_attrs:
                return class_attrs['_singularize']
            return re.sub('(?!^)([A-Z]+)', r'_\1', self.__class__.__name__).lower()
        if name == 'pluralize':
            if '_pluralize' in class_attrs:
                return class_attrs['_pluralize']
            return self.singularize() + 's'
        elif name == 'identifier':
            if '_primary_key' in class_attrs:
                id_field = class_attrs['_primary_key']
            else:
                id_field = self.singularize() + '_id'
            return getattr(self, id_field, None)
        elif '_updatable_attributes' in class_attrs and name in class_attrs['_updatable_attributes']:
            if name in self._json:
                return self._json[name]
            else:
                return None
        elif '_has_one' in class_attrs and name in class_attrs['_has_one']:
            attr = class_attrs['_has_one'][name][0]
            if self._json[attr] is None:
                return None
            cls = class_attrs['_has_one'][name][1]
            if not cls in ApiObject._subclasses:
                raise NameError
            else:
                return cls.from_json(self._json[attr])
        elif '_has_many' in class_attrs and name in class_attrs['_has_many']:
            attr = class_attrs['_has_many'][name]
            results = []
            singular_name = "_".join( [re.sub('s$', '', subname) for subname in attr.split('_') ])
            cls = singular_name.title().translate(None, '_')
            for item in self._json[attr]:
                c = None
                for subclass in ApiObject._subclasses:
                    if cls == subclass.__name__:
                        c = subclass
                if not c:
                    raise NameError
                item_from_uri = \
                    c.from_json(item)
                results.append(item_from_uri)
            return results
        else:
            type(self.__class__).__getattr__(self.__class__, name)

    @classmethod
    def register_subclass(klass, cls):
        klass._subclasses.append(cls)

    @classmethod
    def pluralize(cls):
        return cls.singularize() + 's'

    @classmethod
    def singularize(cls):
        return re.sub('(?!^)([A-Z]+)', r'_\1', cls.__name__).lower()

    @classmethod
    def from_json(cls, data):
        obj = cls(**data)
        obj._json = data
        return obj
    
    def __repr__(self):
        representation = "<%s -- " % (self.__class__.__name__)
        attrs = []
        for attr in self._api_attrs:
            attrs.append("%s:%s" % (attr, repr(getattr(self, attr))))
        return representation + ', '.join(attrs) + '>'
    

class BaseApiObject(JSONObject):

    def __setattr__(self, name, value):
        class_attrs = self.__class__.__dict__
        class_name = self.__class__.__name__

        if '_updatable_attributes' in class_attrs and name in class_attrs['_updatable_attributes']:
            self._api_update(name, value)
            super(BaseApiObject, self).__setattr__(name, value)
        elif name.startswith("_"):
            super(BaseApiObject, self).__setattr__(name, value)
        else:
            raise AttributeError("%s.%s is not an updatable attribute" % (class_name, name))

    @classmethod
    def from_json(cls, data):
        obj = cls(backendSave = False, **data)
        obj._json = data
        return obj

    @classmethod
    def from_uri(cls, uri):
        try:
            result = session.get(uri)
            return cls.from_json(data=result[cls.singularize()])
        except HTTPError, he:
            if he.response.status_code == 404:
                return None
            else:
                raise            
            

    def __init__(self, backendSave=True, **kwargs):
        super(BaseApiObject, self).__init__(**kwargs)
                
        if backendSave:
            self.save()

    def _api_update(self, attr, value):
        data = json.dumps({attr: value}, default=json_default)
        result = session.put(self.url(), data=data)
        self._json = result

    def save(self):
        attributes = {'id': self.identifier}
        attributes.update({attr: getattr(self, attr) for attr in self._api_attrs})        
        data = json.dumps(attributes, default=json_default)
        session.post(self.url(with_id=False), data)

class ApiObject(BaseApiObject):

    def __init__(self, *args, **kwargs):
        super(ApiObject, self).__init__(*args, **kwargs)

    def url(self, with_id = True):
        i = self.identifier
                   
        if with_id:
            i = self.identifier
            id_suffix = "/%s" % i
        else:
            id_suffix = ""
            
        return '%s%s' % (self.pluralize(), id_suffix)
    
    @classmethod
    def from_id(cls, identifier):
        url = cls.pluralize() + '/%s' % identifier
        return cls.from_uri(url)
    
    @classmethod
    def all(cls):
        json = session.get(cls.pluralize())
        return [cls.from_json(o) for o in json[cls.pluralize()]]    


class CourseQualifiedApiObject(BaseApiObject):

    def __init__(self, *args, **kwargs):
        if "course_id" not in kwargs:
            raise AttributeError("CourseQualifiedApiObject constructor did not get a 'course_id' keyword argument") 
        super(CourseQualifiedApiObject, self).__init__(*args, **kwargs)
        
    def url(self, with_id = True):
        i = self.identifier
                
        url_prefix = 'courses/%s/' % self.course_id
            
        if with_id:
            i = self.identifier
            id_suffix = "/%s" % i
        else:
            id_suffix = ""
            
        return '%s%s%s' % (url_prefix, self.pluralize(), id_suffix)   
    
    @classmethod
    def from_id(cls, course_id, identifier):
        url = "courses/%s/%s/%s" % (course_id, cls.pluralize(), identifier)
        return cls.from_uri(url)         
        
    @classmethod
    def all(cls, course_id):
        json = session.get("courses/%s/%s" % (course_id, cls.pluralize()))
        return [cls.from_json(o) for o in json[cls.pluralize()]]        


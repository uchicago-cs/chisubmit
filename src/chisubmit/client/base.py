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


class ApiObject(object):

    __metaclass__ = AttrOverride
    _subclasses = []

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
            if name in self._json_response:
                return self._json_response[name]
            else:
                return None
        elif '_has_one' in class_attrs and name in class_attrs['_has_one']:
            result = None
            result = session.get(('%s/%s') % (self.pluralize(), self.id))
            item = result[self.singularize()][name]
            cls = name.title().translate(None, '_')
            return globals()[cls].from_json(item)
 
        elif '_has_many' in class_attrs and name in class_attrs['_has_many']:
            results = []
            result = session.get(('%s/%s') % (self.pluralize(), self.id))[self.singularize()]
            singular_name = "_".join( [re.sub('s$', '', subname) for subname in name.split('_') ])
            cls = singular_name.title().translate(None, '_')
            for item in result[name]:
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

    def is_course_qualified(self):
        class_attrs = self.__class__.__dict__
        if "_course_qualified" in class_attrs:
            if class_attrs["_course_qualified"]:
                return True
        return False

    def url(self, with_id = True):
        i = self.identifier
                
        if self.is_course_qualified():
            url_prefix = 'courses/%s/' % self.course_id
        else:
            url_prefix = ''
            
        if with_id:
            i = self.identifier
            id_suffix = "/%s" % i
        else:
            id_suffix = ""
            
        return '%s%s%s' % (url_prefix, self.pluralize(), id_suffix)

    @classmethod
    def pluralize(cls):
        return cls.singularize() + 's'

    @classmethod
    def singularize(cls):
        return re.sub('(?!^)([A-Z]+)', r'_\1', cls.__name__).lower()

    @classmethod
    def from_json(cls, data, obj=None):
        cls_data = data
        if not obj:
            obj = cls(backendSave=False, **cls_data)
        obj._json_response = cls_data
        return obj

    @classmethod
    def from_id(cls, identifier):
        url = cls.pluralize() + '/%s' % identifier
        return cls.from_uri(url)

    @classmethod
    def from_course_and_id(cls, course_id, identifier):
        url = "courses/%s/%s/%s" % (course_id, cls.pluralize(), identifier)
        return cls.from_uri(url)
    
    @classmethod
    def all(cls):
        json = session.get(cls.pluralize())
        return [cls.from_json(o) for o in json[cls.pluralize()]]    

    @classmethod
    def all_in_course(cls, course_id):
        json = session.get("courses/%s/%s" % (course_id, cls.pluralize()))
        return [cls.from_json(o) for o in json[cls.pluralize()]]    

    def _api_update(self, attr, value):
        data = json.dumps({attr: value}, default=json_default)
        result = session.put(self.url(), data=data)
        self.__class__.from_json(result, self)

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
            

    def __init__(self, backendSave=True, **kw):
        class_id = self.__class__.__name__.lower() + '_id'
        for attr in self._api_attrs:
            if attr not in kw:
                kw[attr] = None
            setattr(self, attr, kw[attr])
            # FIXME 16JULY14: "alias" the id attribute.
            if attr == class_id:
                self.id = kw[attr]
                
        if self.is_course_qualified():
            self.course_id = kw.get("course_id", None)
                
        if backendSave:
            self.save()

    def save(self):
        attributes = {'id': self.identifier}
        attributes.update({attr: getattr(self, attr) for attr in self._api_attrs})        
        data = json.dumps(attributes, default=json_default)
        session.post(self.url(with_id=False), data)

    def __repr__(self):
        representation = "<%s -- " % (self.__class__.__name__)
        attrs = []
        for attr in self._api_attrs:
            attrs.append("%s:%s" % (attr, repr(getattr(self, attr))))
        return representation + ', '.join(attrs) + '>'

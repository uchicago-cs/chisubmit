
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

import math
import json
from chisubmit.common.utils import set_datetime_timezone_utc
import re
from chisubmit.core import ChisubmitException
from chisubmit.core.client import client
from dateutil.parser import parse
from chisubmit.common.utils import convert_timezone_to_local
from requests import exceptions

# TODO 17DEC14: use the internal config api
api_url = "http://localhost:5000/api/v0/"
client.setup(api_url, 'chudler')

from chisubmit.repos.factory import RemoteRepositoryConnectionFactory


class ChisubmitModelException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class Course(object):

    _updatable_attributes = ('github_organization', 'github_admins_team',
                            'git_server_connection_string', 'git_server_connection_string', 'git_staging_server_connection_string')
    _has_many = ('students', 'projects', 'teams', 'graders', 'instructors')

    def __getattr__(self, name):
        if name in self._updatable_attributes:
            if name in self._json_response:
                return self._json_response[name]
            else:
                # FIXME 23JULY14: there is no possibility it is unfetched?
                return None
        elif name in self._has_many:
            results = []
            result = client.get(('courses/%s') % self.id)['course']
            for item in result[name]:
                # FIXME 22JULY14: very crappy inflection, sorry
                singular_name = "_".join( [re.sub('s$', '', subname) for subname in name.split('_') ])
                # FIXME 22JULY14: assumtion is unlikely to hold
                item_id = singular_name + '_id'
                item_from_uri = \
                    globals()[singular_name.title()].from_json(item)
                # CLI expects to have the items keyed by their id (in a dict)
                results.append(item_from_uri)
            return results
        else:
            raise AttributeError()

    def __setattr__(self, name, value):
        if name in self._updatable_attributes:
            self._api_update(name, value)
        else:
            super(Course, self).__setattr__(name, value)

    def __init__(self, course_id, name, extensions):
        self.course_id = course_id
        self.name = name
        self.extensions = extensions

    def save(self):
        data = json.dumps({'id': self.course_id,
                           'name': self.name, 'extensions': self.extensions})
        client.post('courses', data)
    @staticmethod
    def from_uri(course_uri):
        json = client.get(course_uri)
        return Course.from_json(json)

    @staticmethod
    def from_json(data, course=None):
        course_data = data['course']
        if not course:
            course = \
                Course(course_data['id'], course_data['name'], course_data['extensions'])
        course.id = course_data['id']
        course._json_response = course_data
        return course

    @staticmethod
    def from_course_id(course_id):
        course_uri = 'courses/' + course_id
        return Course.from_uri(course_uri)

    def _api_update(self, attr, value):
        data = json.dumps({attr: value})
        result = client.put('courses/%s' % (self.id),
                           data=data)
        Course.from_json(result, self)

    def get_student(self, student_id):
        return Student.from_uri('courses/%s/students/%s' % (self.id, student_id))

    def add_student(self, student):
        attrs = {'course_id': self.id, 'student_id': student.id}
        data = json.dumps({'students': {'add': [attrs]}})
        client.put('courses/%s' % (self.id), data=data)

    def dropped(self, student):
        client.put('courses/%s/dropped_student/%s' % (self.id,
                                                                  student.id))
    def add_team(self, team):
        attrs = {'course_id': self.id, 'team_id': team.id}
        data = json.dumps({'teams': {'add': [attrs]}})
        client.put('courses/%s' % (self.id), data=data)

    def get_grader(self, grader_id):
        return Grader.from_uri('graders/%s' % (grader_id))

    def add_grader(self, grader):
        attrs = {'course_id': self.id, 'grader_id': grader.id}
        data = json.dumps({'graders': {'add': [attrs]}})
        client.put('courses/%s' % (self.id), data=data)
        
    def get_instructor(self, instructor_id):
        return Instructor.from_uri('instructors/%s' % (instructor_id))
    
    def add_instructor(self, instructor):
        attrs = {'course_id': self.id, 'instructor_id': instructor.id}
        data = json.dumps({'instructors': {'add': [attrs]}})
        client.put('courses/%s' % (self.id), data=data)
 
    # TODO 15JULY14: move this to Project.get() or something similar
    def get_project(self, project_id):
        return Project.from_uri('projects/%s' % (project_id))

    def add_project(self, project):
        attrs = {'course_id': self.id}
        for attr in project._api_attrs:
            if attr == 'deadline':
                attrs[attr] = getattr(project, attr, None).isoformat()
            else:
                attrs[attr] = getattr(project, attr, None)
        # _api_attrs = ('name', 'deadline', 'project_id')
        data = json.dumps({'projects': {'add': [attrs]}})
        client.put('courses/%s' % (self.id), data=data)

    def get_team(self, team_id):
        return Team.from_uri('teams/%s' % (team_id))

    def search_team(self, search_term):
        teams = []
        for t in self.teams.values():
            fields = [t.id, t.private_name]
            for s in t.students:
                fields += [s.first_name, s.last_name, s.github_id]

            for v in fields:
                if search_term.lower() in v.lower():
                    teams.append(t)
                    break

        return teams
    
    def get_git_server_connection(self):
        if self.git_server_connection_string is None:
            raise ChisubmitModelException("Course %s does not have a connection string for its Git server" % (self.id))
        
        conn = RemoteRepositoryConnectionFactory.create_connection(self.git_server_connection_string)
        
        return conn

    def get_git_staging_server_connection(self):
        if self.git_staging_server_connection_string is None:
            raise ChisubmitModelException("Course %s does not have a connection string for its Git staging server" % (self.id))
        
        conn = RemoteRepositoryConnectionFactory.create_connection(self.git_staging_server_connection_string)
        
        return conn
        
        
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


class ApiObject(object):

    __metaclass__ = AttrOverride

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
                return class_attrs['_primary_key']
            return self.singularize() + '_id'
        elif '_updatable_attributes' in class_attrs and name in class_attrs['_updatable_attributes']:
            if name in self._json_response:
                return self._json_response[name]
            else:
                return None
        elif '_has_one' in class_attrs and name in class_attrs['_has_one']:
            result = None
            result = client.get(('%s/%s') % (self.pluralize(), self.id))
            item = result[self.singularize()][name]
            cls = name.title().translate(None, '_')
            return globals()[cls].from_json(item)
 
        elif '_has_many' in class_attrs and name in class_attrs['_has_many']:
            results = []
            result = client.get(('%s/%s') % (self.pluralize(), self.id))[self.singularize()]
            singular_name = "_".join( [re.sub('s$', '', subname) for subname in name.split('_') ])
            cls = singular_name.title().translate(None, '_')
            child_attrs = globals()[cls].__dict__
            if '_primary_key' in child_attrs:
                item_id = child_attrs['_primary_key']
            else:
                item_id = singular_name + '_id'
            for item in result[name]:
                g = globals()
                c = g[cls]
                item_from_uri = \
                    c.from_json(item)
                results.append(item_from_uri)
            return results
        else:
            type(self.__class__).__getattr__(self.__class__, name)

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

    def _api_update(self, attr, value):
        data = json.dumps({attr: value})
        result = client.put('%s/%s' % (self.__class__.pluralize(),
                                                self.id),
                           data=data)
        self.__class__.from_json(result, self)

    @classmethod
    def from_uri(cls, uri):
        result = client.get(uri)
        return cls.from_json(data=result[cls.singularize()])

    def __init__(self, backendSave=True, **kw):
        class_id = self.__class__.__name__.lower() + '_id'
        for attr in self._api_attrs:
            if attr not in kw:
                kw[attr] = None
            setattr(self, attr, kw[attr])
            # FIXME 16JULY14: "alias" the id attribute.
            if attr == class_id:
                self.id = kw[attr]
        if backendSave:
            self.save()

    def save(self):
        attributes = {'id': self.identifier}
        attributes.update({attr: getattr(self, attr) for attr in self._api_attrs})
        data = json.dumps(attributes)
        client.post(type(self).pluralize(), data)

    def __repr__(self):
        representation = "<%s -- " % (self.__class__.__name__)
        attrs = []
        for attr in self._api_attrs:
            attrs.append("%s:%s" % (attr, repr(getattr(self, attr))))
        return representation + ', '.join(attrs) + '>'


class GradeComponent(ApiObject):

    _api_attrs = ('name', 'points')
    _primary_key = 'name'

    @classmethod
    def pluralize(cls):
        return 'grade_components'

    def save(self):
        pass

class Grade(ApiObject):

    _api_attrs = ('points', 'id')
    _updatable_attributes = ('points', )
    _has_one = ('grade_component', )

class Project(ApiObject):

    _api_attrs = ('name', 'deadline', 'id')
    _has_many = ('grade_components', 'teams')

    def __init__(self, **kw):
        for attr in self._api_attrs:
            if attr == 'deadline':
                if hasattr(kw['deadline'], 'isoformat'):
                    self.deadline = kw['deadline']
                else:
                    self.deadline = convert_timezone_to_local(parse(kw['deadline']))
            elif attr == 'id':
              if 'project_id' in kw:
                self.id = kw['project_id']
              else:
                self.id = kw['id']
            else:
                setattr(self, attr, kw[attr])

    def get_grade_component(self, grade_component_name):
        url = 'projects/%s/grade_components/%s' % \
            (self.id, grade_component_name)
        return GradeComponent.from_uri(url)

    def add_grade_component(self, gc):
        attrs = {'project_id': self.id}
        for attr in gc._api_attrs:
            attrs[attr] = getattr(gc, attr, None)
        data = json.dumps({'grade_components': {'add': [attrs]}})
        client.put('projects/%s' % (self.id), data=data)

    def get_deadline(self):
        return self.deadline

    def extensions_needed(self, submission_time):
        delta = (submission_time - self.get_deadline()).total_seconds()

        extensions_needed = math.ceil(delta / (3600.0 * 24))

        if extensions_needed <= 0:
            return 0
        else:
            return int(extensions_needed)

    def get_grading_branch_name(self):
        return self.id + "-grading"

class Person(ApiObject):

    _api_attrs = ('id', 'first_name', 'last_name', 'email', 'git_server_id', 'git_staging_server_id')
    _updatable_attributes = ('git_server_id', 'git_staging_server_id')
    _primary_key = 'person_id'
    _singularize = 'person'
    _pluralize = 'people'

    def save(self):
        try:
          client.get('people/%s' % self.id)
        except exceptions.HTTPError, exception:
            if exception.response.status_code == 404:
                # the person does not exist, so create it
                super(Person, self).save()
            else:
                raise(exception)

    def get_full_name(self, comma = False):
        if comma:
            return "%s, %s" % (self.last_name, self.first_name)
        else:
            return "%s %s" % (self.first_name, self.last_name)

class Student(Person):
    pass

class Grader(Person):
    pass

class Instructor(Person):
    _has_many = ('students', 'projects')
    
class Team(ApiObject):

    _api_attrs = ('id', 'course_id')
    _updatable_attributes = ('private_name', 'git_staging_repo_created', 'git_repo_created', 'active')
    _has_many = ('students', 'projects', 'grades', 'projects_teams')

    def __setattr__(self, name, value):
        if name in self._updatable_attributes:
            self._api_update(name, value)
        else:
            super(Team, self).__setattr__(name, value)

    def add_student(self, student):
        attrs = {'team_id': self.id, 'student_id': student.id}
        data = json.dumps({'students': {'add': [attrs]}})
        client.put('teams/%s' % (self.id), data=data)

    def get_project(self, project_id):
        return next(project_team for project_team in self.projects_teams if project_team.project_id == project_id)

    def add_project(self, project):
        attrs = {'team_id': self.id, 'project_id': project.id}
        data = json.dumps({'projects': {'add': [attrs]}})
        client.put('teams/%s' % (self.id), data=data)

    def has_project(self, project_id):
        try:
            client.get('teams/%s/projects/%s' %
                         (self.id, project_id))
        except exceptions.HTTPError, exception:
            if exception.response.status_code == 404:
                # the project does not exist
                return False
            else:
                raise(exception)
        return True

    def set_project_grade(self, project, grade_component, points):
        assert(isinstance(grade_component, GradeComponent))


        project_team = self.get_project(project.id)
        if not project_team:
            raise ChisubmitModelException("Tried to assign grade, but team %s has not been assigned project %s" %
                                          (self.id, project.id))

        component = project.get_grade_component(grade_component.name)
        
        if not component:
            raise ChisubmitModelException("Tried to assign grade, but project %s does not have grade component %s" %
                                          (project.id, grade_component.name))

        project_team.set_grade(grade_component, points)
        #self.set_grade(component, project_team, points)


class ProjectTeam(ApiObject):
    _api_attrs = ('extensions_used', 'grader_id', 'project_id', 'team_id', 'id')
    _pluralize = 'project_team'
    _has_many = ('grades', )

    def get_grader(self):
        if self.grader_id is None:
            return None
        return Grader.from_uri('graders/%s' % (self.grader_id))

    def add_grader(self, grader):
        attrs = {'grader_id': grader.id}
        data = json.dumps(attrs)
        client.put('teams/%s/projects/%s' % (self.team_id, self.project_id), data=data)

    def set_grade(self, grade_component, points):
        try:
          next(grade for grade in self.grades if grade.grade_component_name == grade_component.name)
          grade.points = points
        except StopIteration:
          # No grade exists for this component and team. Persist a new one
          attrs = {'grade_component_name':grade_component.name, 'points':points}
          data = json.dumps({'grades': {'add': [attrs]}})
          client.put('teams/%s/projects/%s' % (self.team_id, self.project_id), data=data)

    def get_total_penalties(self):
        return sum([p.points for _, p in self.penalties])

    def get_total_grade(self):
        points = sum([p.points for p in self.grades])
        return points #+ self.get_total_penalties()

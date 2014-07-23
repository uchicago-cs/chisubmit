
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
from chisubmit.common.utils import set_datetime_timezone_utc
from chisubmit.core import ChisubmitException
import requests
import json
from datetime import datetime

api_url = "http://localhost:5000/api/%s"


class ChisubmitModelException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class Course(object):

    updatable_attributes = ('github_organization', 'github_admins_team',
                            'git_staging_username', 'git_staging_hostname')
    updatable_children = ('students', 'projects', 'teams', 'graders')

    def __getattr__(self, name):
        if name in self.updatable_attributes:
            if name in self._json_response:
                return self._json_response[name]
            else:
                # FIXME 23JULY14: there is no possibility it is unfetched?
                return None
        elif name in self.updatable_children:
            results = {}
            result = requests.get((api_url % 'courses/%s') % self.id).json()
            for item in result[name]:
                # FIXME 22JULY14: very crappy inflection, sorry
                singular_name = name[:-1]
                # FIXME 22JULY14: assumtion is unlikely to hold
                item_id = singular_name + '_id'
                item_from_uri = \
                    globals()[singular_name.title()].from_json(item)
                # CLI expects to have the items keyed by their id (in a dict)
                results[getattr(item_from_uri, item_id)] = item_from_uri
            return results
        else:
            raise AttributeError()

    def __setattr__(self, name, value):
        if name in self.updatable_attributes:
            self._api_update(name, value)
        else:
            super(Course, self).__setattr__(name, value)

    def __init__(self, course_id, name, extensions):
        self.course_id = course_id
        self.name = name
        self.extensions = extensions

    def save(self):
        data = json.dumps({'course_id': self.course_id,
                           'name': self.name, 'extensions': self.extensions})
        r = requests.post(api_url % 'courses',
                          data, headers={'content-type': 'application/json'})

    @staticmethod
    def from_json(data, course=None):
        if not course:
            course = \
                Course(data['course_id'], data['name'], data['extensions'])
        course.id = data['course_id']
        course._json_response = data
        return course

    @staticmethod
    def from_uri(course_uri):
        r = requests.get(course_uri)
        return Course.from_json(r.json())

    @staticmethod
    def from_course_id(course_id):
        course_uri = api_url % 'courses/' + course_id
        return Course.from_uri(course_uri)

    def _api_update(self, attr, value):
        data = json.dumps({attr: value})
        r = requests.patch(api_url % 'courses/%s' % (self.id),
                           data=data,
                           headers={'content-type': 'application/json'})
        Course.from_json(r.json(), self)

    def get_student(self, student_id):
        return Student.from_uri(api_url % 'students/%s' % (student_id))

    def add_student(self, student):
        attrs = {'course_id': self.id, 'student_id': student.id}
        data = json.dumps({'students': {'add': [attrs]}})
        r = requests.put(api_url % 'courses/%s' % (self.id),
                         data=data,
                         headers={'content-type': 'application/json'})

    def dropped(self, student):
        requests.put(api_url % 'courses/%s/dropped_student/%s' % (self.id,
                                                                  student.id))

    def get_grader(self, grader_id):
        return Grader.from_uri(api_url % 'graders/%s' % (grader_id))

    def add_grader(self, grader):
        attrs = {'course_id': self.id, 'grader_id': grader.id}
        data = json.dumps({'graders': {'add': [attrs]}})
        r = requests.put(api_url % 'courses/%s' % (self.id),
                         data=data,
                         headers={'content-type': 'application/json'})

    # TODO 15JULY14: move this to Project.get() or something similar
    def get_project(self, project_id):
        return Project.from_uri(api_url % 'projects/%s' % (project_id))

    def add_project(self, project):
        attrs = {'course_id': self.id}
        for attr in project.api_attrs:
            if attr == 'deadline':
                attrs[attr] = getattr(project, attr, None).isoformat()
            else:
                attrs[attr] = getattr(project, attr, None)
        # api_attrs = ('name', 'deadline', 'project_id')
        data = json.dumps({'projects': {'add': [attrs]}})
        requests.put(api_url % 'courses/%s' % (self.id),
                     data=data, headers={'content-type': 'application/json'})

    def get_team(self, team_id):
        return Team.from_uri(api_url % 'teams/%s' % (team_id))

    def add_team(self, team):
        attrs = {'course_id': self.id}
        for attr in team.api_attrs:
            attrs[attr] = getattr(team, attr, None)
        data = json.dumps({'teams': {'add': [attrs]}})
        r = requests.put(api_url % 'courses/%s' % (self.id),
                         data=data,
                         headers={'content-type': 'application/json'})

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


class AttrOverride(type):

    def __getattr__(self, name):
        if name == 'pluralize':
            return self.__class__.__name__.lower() + 's'
        elif name == 'identifier':
            return self.__class__.__name__.lower() + '_id'
        else:
            raise AttributeError()


class ApiObject(object):

    __metaclass__ = AttrOverride

    def __getattr__(self, name):
        if name == 'pluralize':
            return self.__class__.__name__.lower() + 's'
        elif name == 'identifier':
            return self.__class__.__name__.lower() + '_id'
        elif name in self.updatable_attributes:
            if name in self._json_response:
                return self._json_response[name]
            else:
                return None
        elif name in self.updatable_children:
            results = []
            r = requests.get((api_url % 'teams/%s') % self.id)
            result = r.json()
            for item in result[name]:
                singular_name = name[:-1]
                item_id = singular_name + '_id'
                item_from_uri = \
                    globals()[singular_name.title()].from_id(item[item_id])
                results.append(item_from_uri)
            return results
        else:
            type(self.__class__).__getattr__(self.__class__, name)

    @classmethod
    def pluralize(cls):
        return cls.__name__.lower() + 's'

    @classmethod
    def from_json(cls, data, obj=None):
        if not obj:
            obj = cls(**data)
        obj._json_response = data
        return obj

    @classmethod
    def from_id(cls, identifier):
        url = api_url % cls.pluralize() + '/%s' % identifier
        return cls.from_uri(url)

    def _api_update(self, attr, value):
        data = json.dumps({attr: value})
        r = requests.patch(api_url % '%s/%s' % (self.__class__.pluralize(),
                                                self.id),
                           data=data,
                           headers={'content-type': 'application/json'})
        self.__class__.from_json(r.json(), self)

    @classmethod
    def from_uri(cls, uri):
        r = requests.get(uri)
        return cls.from_json(data=r.json())

    def __init__(self, **kw):
        class_id = self.__class__.__name__.lower() + '_id'
        for attr in self.api_attrs:
            if attr not in kw:
                kw[attr] = None
            setattr(self, attr, kw[attr])
            # FIXME 16JULY14: "alias" the id attribute.
            # This is a hack. *this* internal API of the CLI should use id
            # or ${model}_id.
            # The problem arrises because the backend wants to use "id"
            # to refer to the database row by that name (which may not exist),
            # which has no relation to the id used by this client
            if attr == class_id:
                self.id = kw[attr]
        self.save()

    def save(self):
        attributes = {attr: getattr(self, attr) for attr in self.api_attrs}
        data = json.dumps(attributes)
        requests.post(api_url % type(self).__name__.lower() + 's', data,
                      headers={'content-type': 'application/json'})

    def __repr__(self):
        representation = "<%s %s -- " % (self.__class__.__name__, self.id)
        attrs = []
        for attr in self.api_attrs:
            attrs.append("%s:%s" % (attr, repr(getattr(self, attr))))
        return representation + ', '.join(attrs) + '>'


class GradeComponent(ApiObject):

    api_attrs = ('name', 'points')

    def save(self):
        pass


class Project(ApiObject):

    api_attrs = ('name', 'deadline', 'project_id')

    def __init__(self, **kw):
        for attr in self.api_attrs:
            if attr == 'deadline':
                if hasattr(kw['deadline'], 'isoformat'):
                    self.deadline = kw['deadline']
                else:
                    self.deadline = datetime.strptime(kw['deadline'],
                                                      '%Y-%m-%dT%H:%M:%S')
            else:
                setattr(self, attr, kw[attr])
        self.id = kw['project_id']

    def get_grade_component(self, grade_component_name):
        url = api_url % 'projects/%s/grade_components/%s' % \
            (project_id, grade_component_name)
        return GradeComponent.from_uri(url)

    def add_grade_component(self, gc):
        attrs = {'project_id': self.id}
        for attr in gc.api_attrs:
            attrs[attr] = getattr(gc, attr, None)
        data = json.dumps({'grade_components': {'add': [attrs]}})
        r = requests.put(api_url % 'projects/%s' % (self.id),
                         data=data,
                         headers={'content-type': 'application/json'})

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
        return self.project_id + "-grading"


class Student(ApiObject):

    api_attrs = ('student_id', 'first_name', 'last_name', 'email', 'github_id')

    def save(self):
        r = requests.get(api_url % 'students/%s' % self.student_id)
        if r.status_code == 404:
            super(Student, self).save()

    def get_full_name(self, comma=False):
        if comma:
            return "%s, %s" % (self.last_name, self.first_name)
        else:
            return "%s %s" % (self.first_name, self.last_name)


class Grader(ApiObject):

    api_attrs = ('grader_id', 'first_name', 'last_name', 'email', 'github_id')

    def get_full_name(self, comma=False):
        if comma:
            return "%s, %s" % (self.last_name, self.first_name)
        else:
            return "%s %s" % (self.first_name, self.last_name)


class Team(ApiObject):

    api_attrs = ('team_id',)
    updatable_attributes = ('github_repo', 'github_team',
                            'private_name', 'github_email_sent', 'active')
    updatable_children = ('students', 'projects')

    def __setattr__(self, name, value):
        if name in self.updatable_attributes:
            self._api_update(name, value)
        else:
            super(Team, self).__setattr__(name, value)

    def save(self):
        pass

    def add_student(self, student):
        attrs = {'team_id': self.id, 'student_id': student.id}
        data = json.dumps({'students': {'add': [attrs]}})
        r = requests.put(api_url % 'teams/%s' % (self.id),
                         data=data,
                         headers={'content-type': 'application/json'})

    def get_project(self, project_id):
        return self.projects.get(project_id)

    def add_project(self, project):
        attrs = {'team_id': self.id, 'project_id': project.id}
        data = json.dumps({'projects': {'add': [attrs]}})
        r = requests.put(api_url % 'teams/%s' % (self.id),
                         data=data,
                         headers={'content-type': 'application/json'})

    def has_project(self, project_id):
        r = requests.get(api_url % 'teams/%s/projects/%s' %
                         (self.team_id, project_id))
        return r.status_code != 404

    def set_project_grade(self, project_id, grade_component, points):
        assert(isinstance(grade_component, GradeComponent))

        team_project = self.get_project(project_id)
        if team_project is None:
            raise ChisubmitModelException("Tried to assign grade, but team %s has not been assigned project %s" %
                                          (self.id, project_id))

        project = team_project.project

        if grade_component not in project.grade_components:
            raise ChisubmitModelException("Tried to assign grade, but project %s does not have grade component %s" %
                                          (project.id, grade_component.name))

        team_project.set_grade(grade_component, points)


class TeamProject(object):
    def __init__(self, project):
        self.project = project

        self.grader = None
        self.extensions_used = 0
        self.grades = {}
        self.penalties = []

    def __repr__(self):
        return "<TeamProject %s>" % (self.project.id)

    def set_grade(self, grade_component, points):
        assert(isinstance(grade_component, GradeComponent))

        if points < 0 or points > grade_component.points:
            raise ChisubmitModelException("Tried to assign invalid number of points in '%s' (got %.2f, expected 0 <= x <= %.2f)" %
                                          (grade_component.name, points, grade_component.points))

        self.grades[grade_component] = points

    def add_penalty(self, description, points):
        if points >= 0:
            raise ChisubmitModelException("Tried to assign a non-negative penalty (%i points: %s)" %
                                          (points, description))
        self.penalties.append((description, points))

    def get_total_penalties(self):
        return sum([p for _, p in self.penalties])

    def get_total_grade(self):
        points = sum([p for p in self.grades.values()])

        return points + self.get_total_penalties()

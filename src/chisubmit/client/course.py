
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
from chisubmit.client.user import Grader
from chisubmit.client.user import Instructor
from chisubmit.client.user import Student
from chisubmit.client.assignment import Assignment
from chisubmit.client.team import Team
from chisubmit.client import session
from requests.exceptions import HTTPError


# TODO 18DEC14: integrate with the base ApiObject class
class Course(object):

    _updatable_attributes = ('git_server_connection_string', 'git_staging_server_connection_string')
    _has_many = ('students', 'assignments', 'teams', 'graders', 'instructors')

    def __getattr__(self, name):
        if name in self._updatable_attributes:
            if name in self._json_response:
                return self._json_response[name]
            else:
                # FIXME 23JULY14: there is no possibility it is unfetched?
                return None
        elif name in self._has_many:
            results = []
            result = session.get(('courses/%s') % self.id)['course']
            for item in result[name]:
                # FIXME 22JULY14: very crappy inflection, sorry
                singular_name = "_".join( [re.sub('s$', '', subname) for subname in name.split('_') ])
                # FIXME 22JULY14: assumtion is unlikely to hold
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

    def __init__(self, course_id, name, options = {}):
        self.course_id = course_id
        self.name = name
        self.options = options

    def save(self):
        data = json.dumps({'id': self.course_id,
                           'name': self.name,
                           'options': self.options})
        session.post('courses', data)

    @staticmethod
    def all():
        json = session.get("courses")
        return [Course.from_json(c, obj_only = True) for c in json["courses"]]

    @staticmethod
    def from_uri(course_uri):
        json = session.get(course_uri)
        return Course.from_json(json)

    @staticmethod
    def from_json(data, course=None, obj_only = False):
        if obj_only:
            course_data = data
        else:
            course_data = data['course']
        if not course:
            course = \
                Course(course_data['id'], course_data['name'], course_data['options'])
        course.id = course_data['id']
        course._json_response = course_data
        return course

    @staticmethod
    def from_course_id(course_id):
        course_uri = 'courses/' + course_id
        return Course.from_uri(course_uri)

    def _api_update(self, attr, value):
        data = json.dumps({attr: value})
        result = session.put('courses/%s' % (self.id),
                           data=data)
        Course.from_json(result, self)

    def get_student(self, student_id):
        return Student.from_uri('courses/%s/students/%s' % (self.id, student_id))

    def add_student(self, student):
        attrs = {'course_id': self.id, 'student_id': student.id}
        data = json.dumps({'students': {'add': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)

    def dropped(self, student):
        session.put('courses/%s/dropped_student/%s' % (self.id,
                                                                  student.id))
    def add_team(self, team):
        attrs = {'course_id': self.id, 'team_id': team.id}
        data = json.dumps({'teams': {'add': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)

    def get_grader(self, grader_id):
        return Grader.from_uri('graders/%s' % (grader_id))

    def add_grader(self, grader):
        attrs = {'course_id': self.id, 'grader_id': grader.id}
        data = json.dumps({'graders': {'add': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)
        
    def get_instructor(self, instructor_id):
        return Instructor.from_uri('instructors/%s' % (instructor_id))
    
    def add_instructor(self, instructor):
        attrs = {'course_id': self.id, 'instructor_id': instructor.id}
        data = json.dumps({'instructors': {'add': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)
        
    def set_option(self, name, value):
        attrs = {'name': name, 'value': value}
        data = json.dumps({'options': {'update': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)        
 
    # TODO 15JULY14: move this to Assignment.get() or something similar
    def get_assignment(self, assignment_id):
        return Assignment.from_course_and_id(self.id, assignment_id)

    def add_assignment(self, assignment):
        attrs = {'course_id': self.id}
        for attr in assignment._api_attrs:
            if attr == 'deadline':
                attrs[attr] = getattr(assignment, attr, None).isoformat()
            else:
                attrs[attr] = getattr(assignment, attr, None)
        # _api_attrs = ('name', 'deadline', 'assignment_id')
        data = json.dumps({'assignments': {'add': [attrs]}})
        session.put('courses/%s' % (self.id), data=data)

    def get_team(self, team_id):
        return Team.from_course_and_id(self.id, team_id) 

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

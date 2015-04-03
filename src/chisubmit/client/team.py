
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

from chisubmit.client import CourseQualifiedApiObject, JSONObject
from chisubmit.client import session
from chisubmit.client.user import User
import json
from chisubmit.common.utils import convert_datetime_to_utc, get_datetime_now_utc
from dateutil import parser
from datetime import timedelta

class Grade(JSONObject):
    
    _api_attrs = ('points','grade_component_id')

class StudentTeam(JSONObject):
    
    _api_attrs = ('status',)
    _has_one = {'user': ('student', User)}

class AssignmentTeam(JSONObject):
    
    _api_attrs = ('extensions_used', 'commit_sha', 'submitted_at', 'assignment_id', 'penalties')
    _has_one = {'grader': ('grader', User)}
    _has_many = {'grades': 'grades'}
    
    def __init__(self, *args, **kwargs):
        if kwargs.has_key("submitted_at"):
            if kwargs["submitted_at"] is not None and not hasattr(kwargs["submitted_at"], 'isoformat'):
                kwargs["submitted_at"] = convert_datetime_to_utc(parser.parse(kwargs['submitted_at']))
                
        super(AssignmentTeam, self).__init__(*args, **kwargs)    
    
    def get_total_penalties(self):
        return sum([p for p in self.penalties.values()])
        
    def get_total_grade(self):
        points = sum([g.points for g in self.grades])
                
        return points + self.get_total_penalties()
    

    
class Team(CourseQualifiedApiObject):

    _api_attrs = ('id', 'active', 'course_id', 'extensions_available', 'extras')
    _primary_key = 'id'    
    _updatable_attributes = ('active',)
    _has_many = {'students': 'students_teams',
                 'assignments': 'assignments_teams',
                 }    
    
    def has_assignment(self, assignment_id):        
        return self.get_assignment(assignment_id) is not None    
    
    def get_assignment(self, assignment_id):
        ats = [at for at in self.assignments if at.assignment_id == assignment_id]
        
        if len(ats) == 1:
            return ats[0]
        else:
            return None        
        
    def has_submitted(self, assignment_id):
        assignment = self.get_assignment(assignment_id)
        if assignment is None:
            return False
        else:
            if assignment.submitted_at is not None:
                return True
            else:
                return False        
        
    def has_assignment_ready_for_grading(self, assignment, when=None):
        ta = self.get_assignment(assignment.id)
        
        if ta is None:
            return False
        
        if ta.submitted_at is None:
            return False
        
        if when is None:
            when = get_datetime_now_utc()
            
        deadline = assignment.deadline + timedelta(days=ta.extensions_used)
        
        if when > deadline:
            return True
        else:
            return False
    
    def add_student(self, student):
        attrs = {'team_id': self.id, 'student_id': student.id}
        data = json.dumps({'students': {'add': [attrs]}})
        session.put(self.url(), data=data)

    def add_assignment(self, assignment):
        attrs = {'team_id': self.id, 'assignment_id': assignment.id}
        data = json.dumps({'assignments': {'add': [attrs]}})
        session.put(self.url(), data=data)

    def set_assignment_grade(self, assignment_id, grade_component_id, points):
        attrs = {'assignment_id': assignment_id, 'grade_component_id': grade_component_id, 'points': points}
        data = json.dumps({'grades': {'add': [attrs]}})
        session.put(self.url(), data=data)

    def set_assignment_penalties(self, assignment_id, penalties):
        attrs = {'assignment_id': assignment_id, 'penalties': penalties}
        data = json.dumps({'grades': {'penalties': [attrs]}})
        session.put(self.url(), data=data)
        
    def set_assignment_grader(self, assignment_id, grader_id):
        attrs = {'assignment_id': assignment_id, 'grader_id': grader_id}
        data = json.dumps({'assignments': {'update': [attrs]}})
        session.put(self.url(), data=data)        
        
    def is_complete(self):
        return all([s.status == 1 for s in self.students])
        
    def get_confirmed_students(self):
        return [s for s in self.students if s.status == 1]
    
    def get_unconfirmed_students(self):
        return [s for s in self.students if s.status == 0]            
    
    def set_extra(self, name, value):
        data = {"extras": [ {'name': name, 'value': value} ] }
        data = json.dumps(data)
        session.put(self.url(), data=data) 
    

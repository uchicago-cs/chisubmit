
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
from chisubmit.common.utils import convert_datetime_to_utc
from chisubmit.client import session
from dateutil import parser
import json

class GradeComponent(JSONObject):
    
    _api_attrs = ('id', 'description', 'points', 'assignment_id')


class Assignment(CourseQualifiedApiObject):

    _api_attrs = ('name', 'deadline', 'id', 'course_id')
    _primary_key = 'id'    
    _has_many = {'grade_components': 'grade_components'}

    def __init__(self, *args, **kwargs):
        if kwargs.has_key("deadline"):
            if not hasattr(kwargs["deadline"], 'isoformat'):
                kwargs["deadline"] = convert_datetime_to_utc(parser.parse(kwargs['deadline']))
                
        super(Assignment, self).__init__(*args, **kwargs)
                
    def register(self, team_name=None, partners = []):
        url = self.url() + "/register"
        data = {}
        if team_name is not None:
            data["team_name"] = team_name
        data["partners"] = partners
        data = json.dumps(data)
        response = session.post(url, data=data)
        return response
    
    def submit(self, team_id, commit_sha, extensions, dry_run):
        url = self.url() + "/submit"
        data = {}
        data["team_id"] = team_id
        data["commit_sha"] = commit_sha
        data["extensions"] = extensions
        data["dry_run"] = dry_run
        data = json.dumps(data)
        response = session.post(url, data=data)
        return response    

    def cancel(self, team_id):
        url = self.url() + "/cancel"
        data = {}
        data["team_id"] = team_id
        data = json.dumps(data)
        response = session.post(url, data=data)
        return response    

    def get_grade_component(self, grade_component_id):
        gcs = [gc for gc in self.grade_components if gc.id == grade_component_id]
        
        if len(gcs) == 0:
            return None
        else:
            return gcs[0]

    def add_grade_component(self, gc):
        attrs = {}
        for attr in gc._api_attrs:
            attrs[attr] = getattr(gc, attr, None)
        data = json.dumps({'grade_components': {'add': [attrs]}})
        session.put(self.url(), data=data)

    def get_deadline(self):
        return self.deadline

    def get_grading_branch_name(self):
        return self.id + "-grading"

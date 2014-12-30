
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

from chisubmit.client.base import ApiObject
from chisubmit.client.grade_component import GradeComponent
from chisubmit.common.utils import convert_timezone_to_local
from chisubmit.client import session
from dateutil import parser
import json
import math

class Assignment(ApiObject):

    _api_attrs = ('name', 'deadline', 'id')
    _has_many = ('grade_components', 'teams')
    _course_qualified = True

    def __init__(self, **kw):
        backendSave = kw.pop("backendSave", True)
        
        ApiObject.__init__(self, backendSave = False, **kw)

        for attr in self._api_attrs:
            if attr == 'deadline':
                if hasattr(kw['deadline'], 'isoformat'):
                    self.deadline = kw['deadline']
                else:
                    self.deadline = convert_timezone_to_local(parser.parse(kw['deadline']))
            elif attr == 'id':
                if 'assignment_id' in kw:
                    self.id = kw['assignment_id']
                else:
                    self.id = kw['id']
            else:
                setattr(self, attr, kw[attr])
        
        if backendSave:       
            self.save()
                

    def get_grade_component(self, grade_component_name):
        url = 'assignments/%s/grade_components/%s' % \
            (self.id, grade_component_name)
        return GradeComponent.from_uri(url)

    def add_grade_component(self, gc):
        attrs = {'assignment_id': self.id}
        for attr in gc._api_attrs:
            attrs[attr] = getattr(gc, attr, None)
        data = json.dumps({'grade_components': {'add': [attrs]}})
        session.put('assignments/%s' % (self.id), data=data)

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

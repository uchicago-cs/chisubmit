
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
from chisubmit.client import session
from chisubmit.client.grade_component import GradeComponent
import json

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
        session.put('teams/%s' % (self.id), data=data)

    def get_project(self, project_id):
        return next(project_team for project_team in self.projects_teams if project_team.project_id == project_id)

    def add_project(self, project):
        attrs = {'team_id': self.id, 'project_id': project.id}
        data = json.dumps({'projects': {'add': [attrs]}})
        session.put('teams/%s' % (self.id), data=data)

    def has_project(self, project_id):
        return session.exists('teams/%s/projects/%s' %
                         (self.id, project_id))

    def set_project_grade(self, project, grade_component, points):
        assert(isinstance(grade_component, GradeComponent))

        project_team = self.get_project(project.id)
        project_team.set_grade(grade_component, points)

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

import chisubmit.client.users
import chisubmit.client.assignment
import chisubmit.client.team
from chisubmit.client.types import ChisubmitAPIObject, Attribute, AttributeType,\
    APIStringType, APIIntegerType
from chisubmit.client.users import User
import datetime

class Course(ChisubmitAPIObject):
    
    _api_attributes = {"url": Attribute(name="url", 
                                   attrtype=APIStringType, 
                                   editable=False),    
    
                       "course_id": Attribute(name="course_id", 
                                       attrtype=APIStringType, 
                                       editable=True),    
        
                       "name": Attribute(name="name", 
                                         attrtype=APIStringType, 
                                         editable=True),    

                       "git_server_connstr": Attribute(name="git_server_connstr", 
                                                  attrtype=APIStringType, 
                                                  editable=True),    

                       "git_staging_connstr": Attribute(name="git_staging_connstr", 
                                                  attrtype=APIStringType, 
                                                  editable=True),    
        
                       "git_usernames": Attribute(name="git_usernames", 
                                                  attrtype=APIStringType, 
                                                  editable=True),    
        
                       "git_staging_usernames": Attribute(name="git_staging_usernames", 
                                                          attrtype=APIStringType, 
                                                          editable=True),    
        
                       "extension_policy": Attribute(name="extension_policy", 
                                                     attrtype=APIStringType, 
                                                     editable=True),    
        
                       "default_extensions": Attribute(name="default_extensions", 
                                                       attrtype=APIIntegerType, 
                                                       editable=True),
                       
                       "instructors_url": Attribute(name="instructors_url", 
                                                    attrtype=APIStringType, 
                                                    editable=False),
                       
                       "graders_url": Attribute(name="graders_url", 
                                                    attrtype=APIStringType, 
                                                    editable=False),       
                       
                       "students_url": Attribute(name="students_url", 
                                                    attrtype=APIStringType, 
                                                    editable=False),                                                                                

                       "assignments_url": Attribute(name="assignments_url", 
                                                    attrtype=APIStringType, 
                                                    editable=False),                                                                                
                       
                       "teams_url": Attribute(name="teams_url", 
                                                    attrtype=APIStringType, 
                                                    editable=False),                                                                                
                      }


    def get_instructors(self):
        """
        :calls: GET /courses/:course/instructors/
        :rtype: List of :class:`chisubmit.client.users.Instructor`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.course_id + "/instructors/"
        )
        return [chisubmit.client.users.Instructor(self._api_client, headers, elem) for elem in data]

    def get_instructor(self, username):
        """
        :calls: GET /courses/:course/instructors/:instructor
        :rtype: :class:`chisubmit.client.users.Instructor`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.course_id + "/instructors/" + username
        )
        return chisubmit.client.users.Instructor(self._api_client, headers, data)
    
    def add_instructor(self, user_or_username, git_username = None, git_staging_username = None):
        """
        :calls: POST /courses/:course/instructors/
        :rtype: :class:`chisubmit.client.users.Instructor`
        """
        
        assert isinstance(user_or_username, (str, unicode)) or isinstance(user_or_username, User) 
        
        if isinstance(user_or_username, (str, unicode)):
            username = user_or_username
        elif isinstance(user_or_username, User):
            username = user_or_username.username
        
        post_data = {"username": username}
        
        if git_username is not None:
            post_data["git_username"] = git_username
        if git_staging_username is not None:
            post_data["git_staging_username"] = git_staging_username
        
        headers, data = self._api_client._requester.request(
            "POST",
            "/courses/" + self.course_id + "/instructors/",
            data = post_data
        )
        return chisubmit.client.users.Instructor(self._api_client, headers, data)    
    
    def remove_instructor(self, user_or_username):
        """
        :calls: DELETE /courses/:course/instructors/:username
        :rtype: None
        """
        
        assert isinstance(user_or_username, (str, unicode)) or isinstance(user_or_username, User) or isinstance(user_or_username, chisubmit.client.users.Instructor)
        
        if isinstance(user_or_username, (str, unicode)):
            username = user_or_username
        elif isinstance(user_or_username, User):
            username = user_or_username.username
        elif isinstance(user_or_username, chisubmit.client.users.Instructor):
            username = user_or_username.user.username
        
        _ = self._api_client._requester.request(
            "DELETE",
            "/courses/" + self.course_id + "/instructors/" + username
        )
        return None
    
    def get_graders(self):
        """
        :calls: GET /courses/:course/graders/
        :rtype: List of :class:`chisubmit.client.users.Grader`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.course_id + "/graders/"
        )
        return [chisubmit.client.users.Grader(self._api_client, headers, elem) for elem in data]    

    def get_grader(self, username):
        """
        :calls: GET /courses/:course/graders/:grader
        :rtype: :class:`chisubmit.client.users.Grader`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.course_id + "/graders/" + username
        )
        return chisubmit.client.users.Grader(self._api_client, headers, data)    
    
    def add_grader(self, user_or_username, git_username = None, git_staging_username = None):
        """
        :calls: POST /courses/:course/graders/
        :rtype: :class:`chisubmit.client.users.Grader`
        """
        
        assert isinstance(user_or_username, (str, unicode)) or isinstance(user_or_username, User) 
        
        if isinstance(user_or_username, (str, unicode)):
            username = user_or_username
        elif isinstance(user_or_username, User):
            username = user_or_username.username
        
        post_data = {"username": username }
        
        if git_username is not None:
            post_data["git_username"] = git_username
        if git_staging_username is not None:
            post_data["git_staging_username"] = git_staging_username
        
        headers, data = self._api_client._requester.request(
            "POST",
            "/courses/" + self.course_id + "/graders/",
            data = post_data
        )
        return chisubmit.client.users.Grader(self._api_client, headers, data)        
    
    def remove_grader(self, user_or_username):
        """
        :calls: DELETE /courses/:course/graders/:username
        :rtype: None
        """
        
        assert isinstance(user_or_username, (str, unicode)) or isinstance(user_or_username, User) or isinstance(user_or_username, chisubmit.client.users.Grader)
        
        if isinstance(user_or_username, (str, unicode)):
            username = user_or_username
        elif isinstance(user_or_username, User):
            username = user_or_username.username
        elif isinstance(user_or_username, chisubmit.client.users.Grader):
            username = user_or_username.user.username
        
        _ = self._api_client._requester.request(
            "DELETE",
            "/courses/" + self.course_id + "/graders/" + username
        )
        return None
        
    
    def get_students(self):
        """
        :calls: GET /courses/:course/students/
        :rtype: List of :class:`chisubmit.client.users.Student`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.course_id + "/students/"
        )
        return [chisubmit.client.users.Student(self._api_client, headers, elem) for elem in data]    
    
    def get_student(self, username):
        """
        :calls: GET /courses/:course/students/:grader
        :rtype: :class:`chisubmit.client.users.Student`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.course_id + "/students/" + username
        )
        return chisubmit.client.users.Student(self._api_client, headers, data)        
    
    def add_student(self, user_or_username, git_username = None, extensions = None, dropped = None):
        """
        :calls: POST /courses/:course/students/
        :rtype: :class:`chisubmit.client.users.Student`
        """
        
        assert isinstance(user_or_username, (str, unicode)) or isinstance(user_or_username, User) 
        
        if isinstance(user_or_username, (str, unicode)):
            username = user_or_username
        elif isinstance(user_or_username, User):
            username = user_or_username.username
        
        post_data = {"username": username }
        
        if git_username is not None:
            post_data["git_username"] = git_username
        if extensions is not None:
            post_data["extensions"] = extensions
        if dropped is not None:
            post_data["dropped"] = dropped
                    
        headers, data = self._api_client._requester.request(
            "POST",
            "/courses/" + self.course_id + "/students/",
            data = post_data
        )
        return chisubmit.client.users.Student(self._api_client, headers, data)       
    
    def remove_student(self, user_or_username):
        """
        :calls: DELETE /courses/:course/students/:username
        :rtype: None
        """
        
        assert isinstance(user_or_username, (str, unicode)) or isinstance(user_or_username, User) or isinstance(user_or_username, chisubmit.client.users.Student)
        
        if isinstance(user_or_username, (str, unicode)):
            username = user_or_username
        elif isinstance(user_or_username, User):
            username = user_or_username.username
        elif isinstance(user_or_username, chisubmit.client.users.Student):
            username = user_or_username.user.username
        
        _ = self._api_client._requester.request(
            "DELETE",
            "/courses/" + self.course_id + "/students/" + username
        )
        return None      
    
    def get_assignments(self):
        """
        :calls: GET /courses/:course/assignments/
        :rtype: List of :class:`chisubmit.client.assignment.Assignment`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.course_id + "/assignments/"
        )
        return [chisubmit.client.assignment.Assignment(self._api_client, headers, elem) for elem in data]    
    
    def get_assignment(self, assignment_id):
        """
        :calls: GET /courses/:course/assignments/:assignment/
        :rtype: List of :class:`chisubmit.client.assignment.Assignment`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.course_id + "/assignments/" + assignment_id
        )
        return chisubmit.client.assignment.Assignment(self._api_client, headers, data)
    
    def create_assignment(self, assignment_id, name, deadline, min_students = None, max_students = None):
        """
        :calls: POST /courses/:course/assignments/
        :param assignment_id: string
        :param name: string
        :param deadline: string
        :param min_students: int
        :param max_students: int
        :rtype: :class:`chisubmit.client.assignment.Assignment`
        """
        assert isinstance(assignment_id, (str, unicode)), assignment_id
        assert isinstance(deadline, (str, unicode)) or isinstance(deadline, datetime.datetime), deadline
        
        # TODO: Convert/validate date
        if isinstance(deadline, (str, unicode)):
            # TODO: validate date
            deadline_str = deadline
        elif isinstance(deadline, datetime.datetime):
            deadline_str = deadline.isoformat(sep=" ")
        
        post_data = {"assignment_id": assignment_id,
                     "name": name,
                     "deadline": deadline_str}
        
        if min_students is not None:
            post_data["min_students"] = min_students
        if max_students is not None:
            post_data["max_students"] = max_students
        
        headers, data = self._api_client._requester.request(
            "POST",
            "/courses/" + self.course_id + "/assignments/",
            data = post_data
        )
        return chisubmit.client.assignment.Assignment(self._api_client, headers, data)    
    
    def get_teams(self):
        """
        :calls: GET /courses/:course/teams/
        :rtype: List of :class:`chisubmit.client.team.Team`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            self.teams_url
        )
        return [chisubmit.client.team.Team(self._api_client, headers, elem) for elem in data]        
    
    def get_team(self, team_id):
        """
        :calls: GET /courses/:course/teams/
        :rtype: :class:`chisubmit.client.team.Team`
        """
        
        assert isinstance(team_id, (str, unicode)), team_id
        
        headers, data = self._api_client._requester.request(
            "GET",
            self.teams_url + team_id
        )
        return chisubmit.client.team.Team(self._api_client, headers, data)    
    
    def create_team(self, team_id, extensions = None, active = None):
        """
        :calls: POST /courses/:course/teams/
        :param name: string
        :param extensions: int
        :param active: bool
        :rtype: :class:`chisubmit.client.team.Team`
        """
        assert isinstance(team_id, (str, unicode)), team_id

        post_data = { "team_id": team_id }
        
        if extensions is not None:
            post_data["extensions"] = extensions
        if active is not None:
            post_data["active"] = active
        
        headers, data = self._api_client._requester.request(
            "POST",
            self.teams_url,
            data = post_data
        )
        return chisubmit.client.team.Team(self._api_client, headers, data)        
    

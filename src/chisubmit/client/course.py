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
from chisubmit.client.types import ChisubmitAPIObject, Attribute, AttributeType,\
    APIStringType, APIIntegerType
from chisubmit.client.users import User

class Course(ChisubmitAPIObject):
    
    _api_attributes = {"url": Attribute(name="url", 
                                   attrtype=APIStringType, 
                                   editable=False),    
    
                       "shortname": Attribute(name="shortname", 
                                       attrtype=APIStringType, 
                                       editable=True),    
        
                       "name": Attribute(name="name", 
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
            "/courses/" + self.shortname + "/instructors/"
        )
        return [chisubmit.client.users.Instructor(self._api_client, headers, elem) for elem in data]
    
    def get_graders(self):
        """
        :calls: GET /courses/:course/graders/
        :rtype: List of :class:`chisubmit.client.users.Grader`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.shortname + "/graders/"
        )
        return [chisubmit.client.users.Grader(self._api_client, headers, elem) for elem in data]    
    
    def get_students(self):
        """
        :calls: GET /courses/:course/students/
        :rtype: List of :class:`chisubmit.client.users.Student`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.shortname + "/students/"
        )
        return [chisubmit.client.users.Student(self._api_client, headers, elem) for elem in data]    
    
    def get_assignments(self):
        """
        :calls: GET /courses/:course/assignments/
        :rtype: List of :class:`chisubmit.client.assignment.Assignment`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.shortname + "/assignments/"
        )
        return [chisubmit.client.assignment.Assignment(self._api_client, headers, elem) for elem in data]    
    
    def get_assignment(self, assignment_id):
        """
        :calls: GET /courses/:course/assignments/:assignment/
        :rtype: List of :class:`chisubmit.client.assignment.Assignment`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.shortname + "/assignments/" + assignment_id
        )
        return chisubmit.client.assignment.Assignment(self._api_client, headers, data)       
    
    def get_teams(self):
        """
        :calls: GET /courses/:course/teams/
        :rtype: List of :class:`chisubmit.client.team.Team`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            "/courses/" + self.shortname + "/teams/"
        )
        return [chisubmit.client.team.Team(self._api_client, headers, elem) for elem in data]                    
    

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

from chisubmit.client.types import ChisubmitAPIObject, Attribute, APIStringType,\
    APIIntegerType, APIBooleanType, APIObjectType
from chisubmit.client.users import Student, User, Grader
from chisubmit.client.assignment import Assignment


class Team(ChisubmitAPIObject):

    _api_attributes = {"url": Attribute(name="url", 
                                       attrtype=APIStringType, 
                                       editable=False),

                       "students_url": Attribute(name="students_url", 
                                                 attrtype=APIStringType, 
                                                 editable=False),  
                       
                       "assignments_url": Attribute(name="assignments_url", 
                                                    attrtype=APIStringType, 
                                                    editable=False),  
                       
                       "name": Attribute(name="name", 
                                         attrtype=APIStringType, 
                                         editable=True),  
    
                       "extensions": Attribute(name="extensions", 
                                               attrtype=APIIntegerType, 
                                               editable=True),  
     
                       "active": Attribute(name="active", 
                                           attrtype=APIBooleanType, 
                                           editable=True),
                      }
    
    def get_team_members(self):
        """
        :calls: GET /courses/:course/teams/:team/students/
        :rtype: List of :class:`chisubmit.client.team.TeamMember`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            self.students_url
        )
        return [TeamMember(self._api_client, headers, elem) for elem in data]        
    
    def get_team_member(self, username):
        """
        :calls: GET /courses/:course/teams/:team/students/:username
        :rtype: :class:`chisubmit.client.team.TeamMember`
        """
        
        assert isinstance(username, (str, unicode)), username
        
        headers, data = self._api_client._requester.request(
            "GET",
            self.students_url + username
        )
        return TeamMember(self._api_client, headers, data)      
    
    def add_team_member(self, user_or_username, confirmed = None):
        """
        :calls: POST /courses/:course/teams/:team/students/
        :rtype: :class:`chisubmit.client.team.TeamMember`
        """
        
        assert isinstance(user_or_username, (str, unicode)) or isinstance(user_or_username, User) 
        
        if isinstance(user_or_username, (str, unicode)):
            username = user_or_username
        elif isinstance(user_or_username, User):
            username = user_or_username.username
        
        post_data = {"username": username}
        
        if confirmed is not None:
            post_data["confirmed"] = confirmed
        
        headers, data = self._api_client._requester.request(
            "POST",
            self.students_url,
            data = post_data
        )
        return TeamMember(self._api_client, headers, data)         
    
    def get_assignment_registrations(self):
        """
        :calls: GET /courses/:course/teams/:team/assignments/
        :rtype: List of :class:`chisubmit.client.team.Registration`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            self.assignments_url
        )
        return [Registration(self._api_client, headers, elem) for elem in data]        
    
    def get_assignment_registration(self, assignment_id):
        """
        :calls: GET /courses/:course/teams/:team/assignments/:assignment
        :rtype: :class:`chisubmit.client.team.Registration`
        """
        
        assert isinstance(assignment_id, (str, unicode)), assignment_id
        
        headers, data = self._api_client._requester.request(
            "GET",
            self.assignments_url + assignment_id
        )
        return Registration(self._api_client, headers, data)     
      
    def add_assignment_registration(self, assignment_or_assignment_id, grader_or_grader_username = None):
        """
        :calls: POST /courses/:course/teams/:team/assignments/
        :rtype: :class:`chisubmit.client.team.Registration`
        """
        
        assert isinstance(assignment_or_assignment_id, (str, unicode)) or isinstance(assignment_or_assignment_id, Assignment) 
        assert grader_or_grader_username is None or isinstance(grader_or_grader_username, (str, unicode)) or isinstance(grader_or_grader_username, Grader) 
        
        if isinstance(assignment_or_assignment_id, (str, unicode)):
            assignment_id = assignment_or_assignment_id
        elif isinstance(assignment_or_assignment_id, User):
            assignment_id = assignment_or_assignment_id.assignment_id
        
        post_data = {"assignment_id": assignment_id}
        
        if grader_or_grader_username is not None:
            if isinstance(grader_or_grader_username, (str, unicode)):
                grader_username = grader_or_grader_username
            elif isinstance(grader_or_grader_username, User):
                grader_username = grader_or_grader_username.user.username
            post_data["grader_username"] = grader_username

        headers, data = self._api_client._requester.request(
            "POST",
            self.assignments_url,
            data = post_data
        )
        return Registration(self._api_client, headers, data)         
    
class TeamMember(ChisubmitAPIObject):

    _api_attributes = {"url": Attribute(name="url", 
                                       attrtype=APIStringType, 
                                       editable=False),

                       "username": Attribute(name="username", 
                                            attrtype=APIStringType, 
                                            editable=False),  
    
                       "student": Attribute(name="student", 
                                            attrtype=APIObjectType(Student), 
                                            editable=False),  
                       
                       "confirmed": Attribute(name="confirmed", 
                                              attrtype=APIBooleanType, 
                                              editable=True),                       
                      }
    
class Registration(ChisubmitAPIObject):

    _api_attributes = {"url": Attribute(name="url", 
                                       attrtype=APIStringType, 
                                       editable=False),

                       "assignment_id": Attribute(name="assignment_id", 
                                                  attrtype=APIStringType, 
                                                  editable=False),  
    
                       "assignment": Attribute(name="assignment", 
                                               attrtype=APIObjectType(Assignment), 
                                               editable=False),  

                       "grader_username": Attribute(name="grader_username", 
                                            attrtype=APIStringType, 
                                            editable=False),  
    
                       "grader": Attribute(name="user", 
                                        attrtype=APIObjectType(Student), 
                                        editable=False),  
                       
                       "confirmed": Attribute(name="confirmed", 
                                              attrtype=APIBooleanType, 
                                              editable=True),                       
                      }        
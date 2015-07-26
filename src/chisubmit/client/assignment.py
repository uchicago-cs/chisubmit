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
    APIIntegerType, APIDateTimeType, APIDecimalType, APIBooleanType,\
    APIObjectType, APIListType

class Assignment(ChisubmitAPIObject):

    _api_attributes = {"url": Attribute(name="url", 
                                       attrtype=APIStringType, 
                                       editable=False),  
                       
                       "rubric_url": Attribute(name="rubric_url", 
                                       attrtype=APIStringType, 
                                       editable=False),                         
                       
                       "assignment_id": Attribute(name="assignment_id", 
                                       attrtype=APIStringType, 
                                       editable=True),  
    
                       "name": Attribute(name="name", 
                                            attrtype=APIStringType, 
                                            editable=True),  
    
                       "deadline": Attribute(name="deadline", 
                                        attrtype=APIDateTimeType, 
                                        editable=True),  
    
                       "min_students": Attribute(name="min_students", 
                                                attrtype=APIIntegerType, 
                                                editable=True),  
     
                       "max_students": Attribute(name="max_students", 
                                               attrtype=APIIntegerType, 
                                               editable=True),
                       
                       "rubric_url": Attribute(name="rubric_url", 
                                                    attrtype=APIStringType, 
                                                    editable=False),                       
                      }
    
    def get_rubric_components(self):
        """
        :calls: GET /courses/:course/assignments/:assignment/rubric
        :rtype: List of :class:`chisubmit.client.assignment.RubricComponent`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            self.rubric_url
        )
        return [RubricComponent(self._api_client, headers, elem) for elem in data]    
    
    
    def create_rubric_component(self, description, points, order = None):
        """
        :calls: POST /courses/:course/assignments/:assignment/rubric/
        :param description: string
        :param points: float
        :param order: int
        :rtype: :class:`chisubmit.client.assignment.RubricComponent`
        """
        assert isinstance(description, (str, unicode)), description
        
        post_data = {"description": description,
                     "points": points}
        
        if order is not None:
            post_data["order"] = order
        
        headers, data = self._api_client._requester.request(
            "POST",
            self.rubric_url,
            data = post_data
        )
        return RubricComponent(self._api_client, headers, data)
    
    def register(self, students):
        """
        :calls: POST /courses/:course/assignments/:assignment/register
        :param students: list of string
        :rtype: :class:`chisubmit.client.assignment.RegistrationResponse`
        """
        assert isinstance(students, (list, tuple)), students
        
        post_data = { "students": students }
        
        headers, data = self._api_client._requester.request(
            "POST",
            self.url + "/register",
            data = post_data
        )
        return RegistrationResponse(self._api_client, headers, data)       
    
class RubricComponent(ChisubmitAPIObject):

    _api_attributes = {"url": Attribute(name="url", 
                                       attrtype=APIStringType, 
                                       editable=False),  

                       "id": Attribute(name="id", 
                                       attrtype=APIIntegerType, 
                                       editable=False),  
                       
                       "description": Attribute(name="name", 
                                                attrtype=APIStringType, 
                                                editable=True),  
    
                       "order": Attribute(name="order", 
                                          attrtype=APIIntegerType, 
                                          editable=True),  
    
                       "points": Attribute(name="points", 
                                           attrtype=APIDecimalType, 
                                           editable=True)
                                              
                      }        
    
class RegistrationResponse(ChisubmitAPIObject):
    
    _api_attributes = {

                       "new_team": Attribute(name="new_team", 
                                         attrtype=APIBooleanType, 
                                         editable=False),  
                       
                       "team": Attribute(name="team", 
                                         attrtype=APIObjectType("chisubmit.client.team.Team"), 
                                         editable=False),  

                       "team_members": Attribute(name="team_members", 
                                         attrtype=APIListType(APIObjectType("chisubmit.client.team.TeamMember")), 
                                         editable=False),

                       "registration": Attribute(name="registration", 
                                          attrtype=APIObjectType("chisubmit.client.team.Registration"), 
                                          editable=False),  
                                              
                      }
    
        
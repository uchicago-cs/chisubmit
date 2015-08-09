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
    APIIntegerType, APIBooleanType, APIObjectType, APIDateTimeType, APIDictType,\
    APIDecimalType
from chisubmit.client.users import Student, User, Grader
from chisubmit.client.assignment import Assignment, RubricComponent
from chisubmit.common.utils import is_submission_ready_for_grading


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
                       
                       "team_id": Attribute(name="team_id", 
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
    
class Submission(ChisubmitAPIObject):

    _api_attributes = {"url": Attribute(name="url", 
                                       attrtype=APIStringType, 
                                       editable=False),

                       "id": Attribute(name="id", 
                                       attrtype=APIIntegerType, 
                                       editable=False),  
    
                       "extensions_used": Attribute(name="extensions_used", 
                                               attrtype=APIIntegerType, 
                                               editable=True),  

                       "commit_sha": Attribute(name="commit_sha", 
                                            attrtype=APIStringType, 
                                            editable=True),  
    
                       "submitted_at": Attribute(name="submitted_at", 
                                        attrtype=APIDateTimeType, 
                                        editable=True)                    
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
                                                    editable=True),  
    
                       "grader": Attribute(name="grader", 
                                        attrtype=APIObjectType(Grader), 
                                        editable=False),  
                       
                       "submissions_url": Attribute(name="submissions_url", 
                                                    attrtype=APIStringType, 
                                                    editable=False),     
                                              
                       "final_submission_id": Attribute(name="final_submission_id", 
                                                     attrtype=APIIntegerType, 
                                                     editable=True),

                       "final_submission": Attribute(name="final_submission", 
                                                     attrtype=APIObjectType(Submission), 
                                                     editable=False),
                       
                       "final_submission_url": Attribute(name="final_submission_url", 
                                                         attrtype=APIStringType, 
                                                         editable=False),                                     

                       "grades_url": Attribute(name="grades_url", 
                                               attrtype=APIStringType, 
                                               editable=False),                                     

                       "grade_adjustments": Attribute(name="grade_adjustments", 
                                                      attrtype=APIDictType(APIDecimalType), 
                                                      editable=True),                                     
                      }
    
    def get_submissions(self):
        """
        :calls: GET /courses/:course/teams/:team/assignments/:assignment/submissions
        :rtype: List of :class:`chisubmit.client.team.Submission`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            self.submissions_url
        )
        return [Submission(self._api_client, headers, elem) for elem in data]        
    
    def get_submission(self, submission):
        """
        :calls: GET /courses/:course/teams/:team/assignments/:assignment/submissions/:submission
        :rtype: :class:`chisubmit.client.team.Submission`
        """
        
        assert isinstance(submission, int), submission
        
        headers, data = self._api_client._requester.request(
            "GET",
            self.submissions_url + str(submission)
        )
        return Submission(self._api_client, headers, data)      
    
    def add_submission(self, commit_sha, extensions_used = None, submitted_at = None):
        """
        :calls: POST /courses/:course/teams/:team/assignments/:assignment/submissions/
        :rtype: :class:`chisubmit.client.team.Submission`
        """
        
        post_data = {"commit_sha": commit_sha}
        
        if extensions_used is not None:
            post_data["extensions_used"] = extensions_used
        if submitted_at is not None:
            post_data["submitted_at"] = submitted_at

        headers, data = self._api_client._requester.request(
            "POST",
            self.submissions_url,
            data = post_data
        )
        return Submission(self._api_client, headers, data)

    def get_grades(self):
        """
        :calls: GET /courses/:course/teams/:team/assignments/:assignment/grades/
        :rtype: List of :class:`chisubmit.client.team.Grade`
        """
        
        headers, data = self._api_client._requester.request(
            "GET",
            self.grades_url
        )
        return [Grade(self._api_client, headers, elem) for elem in data]            
    
    def add_grade(self, rubric_component, points = None):
        """
        :calls: POST /courses/:course/teams/:team/assignments/:assignment/grades/
        :rtype: :class:`chisubmit.client.team.Grade`
        """
        
        post_data = {"rubric_component_id": rubric_component.id}
        
        if points is not None:
            post_data["points"] = points

        headers, data = self._api_client._requester.request(
            "POST",
            self.grades_url,
            data = post_data
        )
        return Grade(self._api_client, headers, data)

    
    def submit(self, commit_sha, extensions, ignore_deadline = False, dry_run=False):
        """
        :calls: POST /courses/:course/teams/:team/assignments/:assignment/submit/
        :rtype: :class:`chisubmit.client.team.Submission`
        """
        
        post_data = {"commit_sha": commit_sha,
                     "extensions": extensions,
                     "ignore_deadline": ignore_deadline}
        
        if dry_run:
            qs = "?dry_run=true"
        else:
            qs = ""
        
        headers, data = self._api_client._requester.request(
            "POST",
            self.url + "/submit"+qs,
            data = post_data
        )
        return SubmissionResponse(self._api_client, headers, data)    

    def set_grade(self, rubric_component, points):
        if points < 0 or points > rubric_component.points:
            raise ValueError("Invalid grade value %.2f ('%s' must be 0 <= x <= %.2f)" % (points, rubric_component.description, rubric_component.points))
        
        grades = self.get_grades()
        grade = [g for g in grades if g.rubric_component_id == rubric_component.id]
        
        if len(grade) == 0:
            self.add_grade(rubric_component, points)
        elif len(grade) == 1:
            grade[0].points = points
        else:
            msg = "Server returned more than one grade for '%s' in %s. " % (rubric_component.description, self.assignment.assignment_id)
            msg += "This should not happen. Please contact the chisubmit administrator."

            raise Exception(msg)

    def get_total_penalties(self):
        if self.grade_adjustments is None:
            return 0.0
        else:
            return sum([v for v in self.grade_adjustments.values() if v < 0.0])

    def get_total_bonuses(self):
        if self.grade_adjustments is None:
            return 0.0
        else:
            return sum([v for v in self.grade_adjustments.values() if v >= 0.0])
        
    def get_total_adjustments(self):
        if self.grade_adjustments is None:
            return 0.0
        else:
            return sum([v for v in self.grade_adjustments.values()])
    
    def get_total_grade(self):
        grades = self.get_grades()
        
        return sum([g.points for g in grades]) + self.get_total_adjustments()

    def get_grading_branch_name(self):
        return self.assignment.assignment_id + "-grading"
        
    def is_ready_for_grading(self):    
        if self.final_submission is None:
            return False
        else:
            return is_submission_ready_for_grading(assignment_deadline=self.assignment.deadline, 
                                                   submission_date=self.final_submission.submitted_at,
                                                   extensions_used=self.final_submission.extensions_used)    
    
class SubmissionResponse(ChisubmitAPIObject):
    
    _api_attributes = {
                       "submission": Attribute(name="registration", 
                                               attrtype=APIObjectType(Submission), 
                                               editable=False),  
                                              
                       "extensions_before": Attribute(name="extensions_before", 
                                                      attrtype=APIIntegerType, 
                                                      editable=False),  

                       "extensions_after": Attribute(name="extensions_before", 
                                                     attrtype=APIIntegerType, 
                                                     editable=False),  
                       }    
    
    
class Grade(ChisubmitAPIObject):

    _api_attributes = {"url": Attribute(name="url", 
                                       attrtype=APIStringType, 
                                       editable=False),
                       
                       "rubric_component_id": Attribute(name="rubric_component_id", 
                                                        attrtype=APIIntegerType, 
                                                        editable=False),
                             
                       "rubric_component": Attribute(name="rubric_component", 
                                                     attrtype=APIObjectType(RubricComponent), 
                                                     editable=False),   
                       
                       "points": Attribute(name="points", 
                                           attrtype=APIDecimalType, 
                                           editable=True)
                       }                          
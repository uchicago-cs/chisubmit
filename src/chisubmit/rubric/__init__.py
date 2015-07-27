
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

import yaml
import textwrap

def feq(a, b, eps=0.01):
    return abs(a - b) <= eps

class ChisubmitRubricException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class RubricFile(object):
    
    FIELD_COMMENTS = "Comments"
    FIELD_PENALTIES = "Penalties"
    FIELD_BONUSES = "Bonuses"
    FIELD_POINTS   = "Points"
    FIELD_TOTAL_POINTS = "Total Points"
    FIELD_POINTS_POSSIBLE = "Points Possible"
    FIELD_POINTS_OBTAINED = "Points Obtained"
    
    def __init__(self, assignment, rubric_components, points, penalties, bonuses, comments):
        self.assignment = assignment
        self.rubric_components = rubric_components
        self.points = points
        self.penalties = penalties
        self.bonuses = bonuses
        self.comments = comments
        
    def __format_points(self, n):
        return str(round(n,2) if n % 1 else int(n))
        
    def to_yaml(self, include_blank_comments = False):
        # We generate the file manually to make it as human-readable as possible
        
        s = "Points:\n"
        
        total_points_possible = 0
        total_points_obtained = 0
        
        for rc in self.rubric_components:
            s += "%s%s:\n" % (" "*4, rc.description)
            s += "%s%s: %s\n" % (" "*8, self.FIELD_POINTS_POSSIBLE, self.__format_points(rc.points))
            total_points_possible += rc.points
            if self.points[rc.description] is None:
                p = ""
            else:
                total_points_obtained += self.points[rc.description]
                p = self.__format_points(self.points[rc.description])
                
            s += "%s%s: %s\n" % (" "*8, self.FIELD_POINTS_OBTAINED, p)
            s += "\n" 
            
        penalty_points = 0.0
        if self.penalties is not None:
            s += "%s:\n" % self.FIELD_PENALTIES
            for desc, v in self.penalties.items():
                penalty_points += v
                s += "%s%s:%s\n" % (" "*4, desc, self.__format_points(v))            
            s += "\n"

        bonus_points = 0.0
        if self.bonuses is not None:
            s += "%s:\n" % self.FIELD_BONUSES
            for desc, v in self.bonuses.items():
                bonus_points += v
                s += "%s%s:%s\n" % (" "*4, desc, self.__format_points(v))            
            s += "\n"

        s += "%s: %s / %s\n" % (self.FIELD_TOTAL_POINTS,
                              self.__format_points(total_points_obtained + penalty_points + bonus_points),
                              self.__format_points(total_points_possible)) 
            
        if self.comments is not None or include_blank_comments:
            s += "\n"
            s += "%s: >\n" % self.FIELD_COMMENTS
            
            if self.comments is not None:
                for l in self.comments.strip().split("\n"):
                    for l2 in textwrap.wrap(l, initial_indent = " "*4):
                        s += l2 + "\n" 
            else:
                s += " "*4 + "None"
        
        return s
        
    def save(self, rubric_file, include_blank_comments = False):
        try:
            f = open(rubric_file, 'w')
            f.write(self.to_yaml(include_blank_comments))
            f.close()
        except IOError, ioe:
            raise ChisubmitRubricException("Error when saving rubric to file %s: %s" % (rubric_file, ioe.message), ioe)
        
    @classmethod
    def from_file(cls, rubric_file, assignment):
        rubric = yaml.load(rubric_file)

        if not rubric.has_key(RubricFile.FIELD_POINTS):
            raise ChisubmitRubricException("Rubric file doesn't have a '%s' field." % RubricFile.FIELD_POINTS)

        if not rubric.has_key(RubricFile.FIELD_TOTAL_POINTS):
            raise ChisubmitRubricException("Rubric file doesn't have a '%s' field." % RubricFile.FIELD_TOTAL_POINTS)

        points = {}
        total_points_obtained = 0
        total_points_possible = 0
        rubric_components = assignment.get_rubric_components()
        
        for rubric_component in rubric_components:
            if not rubric[RubricFile.FIELD_POINTS].has_key(rubric_component.description):
                raise ChisubmitRubricException("Rubric is missing '%s' points." % rubric_component.description)
            
            component = rubric[RubricFile.FIELD_POINTS][rubric_component.description]
            
            if not component.has_key(RubricFile.FIELD_POINTS_POSSIBLE):
                raise ChisubmitRubricException("Grade component '%s' is missing '%s' field." % (rubric_component.description, RubricFile.FIELD_POINTS_POSSIBLE))

            if not component.has_key(RubricFile.FIELD_POINTS_OBTAINED):
                raise ChisubmitRubricException("Grade component '%s' is missing '%s' field." % (rubric_component.description, RubricFile.FIELD_POINTS_OBTAINED))
            
            points_possible = component[RubricFile.FIELD_POINTS_POSSIBLE]
            points_obtained = component[RubricFile.FIELD_POINTS_OBTAINED]
            
            if points_possible != rubric_component.points:
                raise ChisubmitRubricException("Grade component '%s' in rubric has incorrect possible points (expected %i, got %i)" %
                                                (rubric_component.description, rubric_component.points, points_possible))
                
            if points_obtained is not None:
                if points_obtained < 0:
                    raise ChisubmitRubricException("Grade component '%s' in rubric has negative points (%i)" %
                                                    (rubric_component.description, points_obtained))
    
                if points_obtained > points_possible:
                    raise ChisubmitRubricException("Grade component '%s' in rubric has more than allowed points (%i > %i)" %
                                                    (rubric_component.description, points_obtained, points_possible))

                total_points_obtained += points_obtained

            points[rubric_component.description] = points_obtained
            total_points_possible += rubric_component.points

        penalty_points = 0.0
        if rubric.has_key(RubricFile.FIELD_PENALTIES):
            penalties = rubric[RubricFile.FIELD_PENALTIES]
            for desc, v in penalties.items():
                if v >= 0:
                    raise ChisubmitRubricException("Rubric file has a non-negative penalty: %s (%s)" % (v, desc))
                penalty_points += v
        else:
            penalties = None

        bonus_points = 0.0
        if rubric.has_key(RubricFile.FIELD_BONUSES):
            bonuses = rubric[RubricFile.FIELD_BONUSES]
            for desc, v in bonuses.items():
                if v < 0:
                    raise ChisubmitRubricException("Rubric file has a negative bonus: %s (%s)" % (v, desc))
                bonus_points += v
        else:
            bonuses = None

        total_points_with_adjustments = float(total_points_obtained) + penalty_points + bonus_points

        if type(rubric[RubricFile.FIELD_TOTAL_POINTS]) != str:
            raise ChisubmitRubricException("Total points is not a string: %s" % rubric[RubricFile.FIELD_TOTAL_POINTS])
        
        total_points = rubric[RubricFile.FIELD_TOTAL_POINTS].split(" / ")
        if len(total_points) != 2:
            raise ChisubmitRubricException("Improperly formatted total points: %s" % rubric[RubricFile.FIELD_TOTAL_POINTS])
        
        if not feq(float(total_points[0]), total_points_with_adjustments):
            raise ChisubmitRubricException("Incorrect number of total points obtained (Expected %.2f, got %.2f)" % 
                                           (total_points_with_adjustments, float(total_points[0])))
            
        if not feq(float(total_points[1]), float(total_points_possible)):
            raise ChisubmitRubricException("Incorrect number of total points possible (Expected %.2f, got %.2f)" % 
                                           (float(total_points_possible), float(total_points[1])))
            
        if not rubric.has_key(RubricFile.FIELD_COMMENTS):
            comments = None
        else:
            comments = rubric[RubricFile.FIELD_COMMENTS]

        return cls(assignment, rubric_components, points, penalties, bonuses, comments)

    @classmethod
    def from_assignment(cls, assignment, grades = None):
        rubric_components = assignment.get_rubric_components()
        points = dict([(rc.description, None) for rc in rubric_components])
        
        if grades is not None:
            for grade in grades:
                points[grade.rubric_component.description] = grade.points
        
        return cls(assignment, rubric_components, points, penalties = None, bonuses = None, comments = None)

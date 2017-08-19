
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
from yaml.scanner import ScannerError
import warnings

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
    
    def __init__(self, rubric_components, points_possible, points_obtained, penalties, bonuses, comments):
        self.rubric_components = rubric_components
        self.points_possible = points_possible
        self.points_obtained = points_obtained
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
            s += "%s- %s:\n" % (" "*4, rc)
            s += "%s%s: %s\n" % (" "*8, self.FIELD_POINTS_POSSIBLE, self.__format_points(self.points_possible[rc]))
            total_points_possible += self.points_possible[rc]
            if self.points_obtained[rc] is None:
                p = ""
            else:
                total_points_obtained += self.points_obtained[rc]
                p = self.__format_points(self.points_obtained[rc])
                
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
        
    def validate(self, assignment):
        rubric_components = assignment.get_rubric_components()
        
        for rubric_component in rubric_components:
            if not rubric_component.description in self.rubric_components:
                raise ChisubmitRubricException("Rubric is missing '%s' points." % rubric_component.description)
            
            points_possible = self.points_possible[rubric_component.description]
                        
            if points_possible != rubric_component.points:
                raise ChisubmitRubricException("Grade component '%s' in rubric has incorrect possible points (expected %i, got %i)" %
                                                (rubric_component.description, rubric_component.points, points_possible))
                
    def get_total_points_obtained(self):
        t = sum([p for p in self.points_obtained.values() if p is not None])
        if self.penalties is not None:
            t += sum([p for p in self.penalties.values()])
        if self.bonuses is not None:
            t += sum([p for p in self.bonuses.values()])
        return t
                
    @classmethod
    def from_file(cls, rubric_file, assignment=None):
        try:
            rubric = yaml.load(rubric_file)
        except ScannerError, se:
            raise ChisubmitRubricException("YAML syntax error in rubric file: %s" % str(se)) 

        if not rubric.has_key(RubricFile.FIELD_POINTS):
            raise ChisubmitRubricException("Rubric file doesn't have a '%s' field." % RubricFile.FIELD_POINTS)

        if not rubric.has_key(RubricFile.FIELD_TOTAL_POINTS):
            raise ChisubmitRubricException("Rubric file doesn't have a '%s' field." % RubricFile.FIELD_TOTAL_POINTS)

        rubric_components = []
        points_obtained = {}
        points_possible = {}
        total_points_obtained = 0
        total_points_possible = 0
        
        # Backwards compatibility. rubric[RubricFile.FIELD_POINTS] was originally a dictionary
        if isinstance(rubric[RubricFile.FIELD_POINTS], dict):
            rcs = rubric[RubricFile.FIELD_POINTS].items()
            warnings.warn("You are using a deprecated rubric file format. Please consult the chisubmit documentation.", DeprecationWarning)
        elif isinstance(rubric[RubricFile.FIELD_POINTS], list):
            rcs = []
            for rc in rubric[RubricFile.FIELD_POINTS]:
                if len(rc) != 1:
                    raise ChisubmitRubricException("Incorrect formatting. Every category under '%s' should be indented and start with a hyphen." % RubricFile.FIELD_POINTS)
                for k,v in rc.items():
                    rcs.append((k,v))

        for rc_description, rc in rcs:
                        
            rubric_components.append(rc_description)
                        
            if not rc.has_key(RubricFile.FIELD_POINTS_POSSIBLE):
                raise ChisubmitRubricException("Grade component '%s' is missing '%s' field." % (rc_description, RubricFile.FIELD_POINTS_POSSIBLE))

            if not rc.has_key(RubricFile.FIELD_POINTS_OBTAINED):
                raise ChisubmitRubricException("Grade component '%s' is missing '%s' field." % (rc_description, RubricFile.FIELD_POINTS_OBTAINED))
            
            try:
                rc_points_obtained = rc[RubricFile.FIELD_POINTS_OBTAINED]
                if rc_points_obtained is not None:
                    rc_points_obtained = float(rc_points_obtained)
            except ValueError:
                raise ChisubmitRubricException("Obtained points in grade component '%s' does not appear to be a number: %s" %
                                                (rc_description, rc[RubricFile.FIELD_POINTS_OBTAINED]))

            try:
                rc_points_possible = float(rc[RubricFile.FIELD_POINTS_POSSIBLE])
                if rc_points_possible is not None:
                    rc_points_possible = float(rc_points_possible)
            except ValueError:
                raise ChisubmitRubricException("Possible points in grade component '%s' does not appear to be a number: %s" %
                                                (rc_description, rc[RubricFile.FIELD_POINTS_POSSIBLE]))

            if rc_points_obtained is not None:
                if rc_points_obtained < 0:
                    raise ChisubmitRubricException("Grade component '%s' in rubric has negative points (%i)" %
                                                    (rc_description.description, rc_points_obtained))
    
                if rc_points_obtained > rc_points_possible:
                    raise ChisubmitRubricException("Grade component '%s' in rubric has more than allowed points (%i > %i)" %
                                                    (rc_description.description, rc_points_obtained, rc_points_possible))

                total_points_obtained += rc_points_obtained

            points_obtained[rc_description] = rc_points_obtained
            points_possible[rc_description] = rc_points_possible
            total_points_possible += rc_points_possible

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

        r = cls(rubric_components, points_possible, points_obtained, penalties, bonuses, comments)
        
        if assignment is not None:
            r.validate(assignment)
            
        return r

    @classmethod
    def from_assignment(cls, assignment, grades = None):
        rubric_components = assignment.get_rubric_components()
        rc_descriptions = [rc.description for rc in rubric_components]
        points_obtained = {rc.description: None for rc in rubric_components}
        points_possible = {rc.description: rc.points for rc in rubric_components}
        
        if grades is not None:
            for grade in grades:
                points_obtained[grade.rubric_component.description] = grade.points
        
        return cls(rc_descriptions, points_possible, points_obtained, penalties = None, bonuses = None, comments = None)

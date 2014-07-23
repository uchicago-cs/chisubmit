
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
import math
import os.path
import chisubmit.core
from chisubmit.common.utils import set_datetime_timezone_utc
import urllib2
from chisubmit.core import ChisubmitException
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory


class ChisubmitModelException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class Course(object):
    def __init__(self, course_id, name, extensions):
        self.id = course_id
        self.name = name
        self.extensions = extensions
        
        self.git_server_connection_string = None
        self.git_staging_server_connection_string = None
        
        self.students = {}
        self.graders = {}
        self.instructors = {}
        self.projects = {}
        self.teams = {}
        
        self.course_file = None
        
    def save(self, course_file = None):
        if self.course_file is None and course_file is None:
            raise ChisubmitModelException("Course object has no file associated with it.")

        if course_file is None:
            course_file = self.course_file
            
        try:
            f = open(course_file, 'w')
            yaml.dump(self, f)
            f.close()
        except IOError, ioe:
            raise ChisubmitException("Error when saving course to file %s: %s" % (course_file, ioe.meesage), ioe)
        
    @staticmethod
    def from_file(course_file):
        course = yaml.load(course_file)
        if type(course) != Course:
            raise ChisubmitModelException("Course file does not contain a Course object.")
        return course

    @staticmethod
    def from_url(course_url):
        try:
            req = urllib2.Request(course_url)
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, he:
            raise ChisubmitException("Error when accessing %s: %s %s" % (course_url, he.code, he.msg), he)
        except urllib2.URLError, ue:
            raise ChisubmitException("Error when accessing %s: %s" % (course_url, ue.reason), ue)
        
        course = yaml.load(response)
        if type(course) != Course:
            raise ChisubmitModelException("Course file does not contain a Course object.")        
        
        return course
    
    @staticmethod
    def from_course_id(course_id):
        course_file = chisubmit.core.get_course_filename(course_id)
        if not os.path.exists(course_file):
            return None
        course_file = open(course_file)
        course_obj = Course.from_file(course_file)
        course_file.close()
        return course_obj
    
    def get_student(self, student_id):
        return self.students.get(student_id)
        
    def add_student(self, student):
        self.students[student.id] = student

    def get_grader(self, grader_id):
        return self.graders.get(grader_id)
    
    def add_grader(self, grader):
        self.graders[grader.id] = grader
        
    def get_instructor(self, instructor_id):
        return self.instructors.get(instructor_id)
    
    def add_instructor(self, instructor):
        self.instructors[instructor.id] = instructor        

    def get_project(self, project_id):
        return self.projects.get(project_id)

    def add_project(self, project):
        self.projects[project.id] = project

    def get_team(self, team_id):
        return self.teams.get(team_id)

    def add_team(self, team):
        self.teams[team.id] = team
        
    def search_team(self, search_term):
        teams = []
        for t in self.teams.values():
            fields = [t.id, t.private_name]
            for s in t.students:
                fields += [s.first_name, s.last_name, s.github_id] 
            
            for v in fields:
                if search_term.lower() in v.lower():
                    teams.append(t)
                    break     
        
        return teams
    
    def get_git_server_connection(self):
        if self.git_server_connection_string is None:
            raise ChisubmitModelException("Course %s does not have a connection string for its Git server" % (self.id))
        
        conn = RemoteRepositoryConnectionFactory.create_connection(self.git_server_connection_string)
        
        return conn

    def get_git_staging_server_connection(self):
        if self.git_staging_server_connection_string is None:
            raise ChisubmitModelException("Course %s does not have a connection string for its Git staging server" % (self.id))
        
        conn = RemoteRepositoryConnectionFactory.create_connection(self.git_staging_server_connection_string)
        
        return conn
        
        
class GradeComponent(object):
    def __init__(self, name, points):
        self.name = name
        self.points = points        
        
    def __repr__(self):
        return "<GradeComponent %s (%s points)>" % (self.name, self.points)        


class Project(object):
    def __init__(self, project_id, name, deadline):
        self.id = project_id
        self.name = name
        self.deadline = deadline
        self.grade_components = []
        
    def __repr__(self):
        return "<Project %s: %s>" % (self.id, self.name)        
      
    def get_grade_component(self, grade_component_name):
        gcs = [gc for gc in self.grade_components if gc.name == grade_component_name]
        
        if len(gcs) == 0:
            return None
        elif len(gcs) == 1:
            return gcs[0]
        else:
            raise ChisubmitModelException("Project %s has two grade components with the same name (%s)" % (self.id, grade_component_name))
                
    def add_grade_component(self, grade_component):
        self.grade_components.append(grade_component)

    # We need to do this because PyYAML doesn't load
    # timezone data when reading dates. 
    def get_deadline(self):
        return set_datetime_timezone_utc(self.deadline)
        
    def extensions_needed(self, submission_time):
        delta = (submission_time - self.get_deadline()).total_seconds()
        
        extensions_needed = math.ceil(delta / (3600.0 * 24))
        
        if extensions_needed <= 0:
            return 0
        else:
            return int(extensions_needed)        
        
    def get_grading_branch_name(self):
        return self.id + "-grading"
        

class Student(object):
    def __init__(self, student_id, first_name, last_name, email, git_server_id):
        self.id = student_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.git_server_id = git_server_id
        
        self.dropped = False
        
    def __repr__(self):
        return "<Student %s: %s>" % (self.id, self.get_full_name())
        
    def get_full_name(self, comma = False):
        if comma:
            return "%s, %s" % (self.last_name, self.first_name)
        else:
            return "%s %s" % (self.first_name, self.last_name)
            
        
   
class Grader(object):
    def __init__(self, grader_id, first_name, last_name, email, git_server_id, git_staging_server_id):
        self.id = grader_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.git_server_id = git_server_id
        self.git_staging_server_id = git_staging_server_id
        
        self.conflicts = []
        
    def __repr__(self):
        return "<Grader %s: %s>" % (self.id, self.get_full_name())        
        
    def get_full_name(self, comma = False):
        if comma:
            return "%s, %s" % (self.last_name, self.first_name)
        else:
            return "%s %s" % (self.first_name, self.last_name)        

class Instructor(object):
    def __init__(self, instructor_id, first_name, last_name, email, git_server_id, git_staging_server_id):
        self.id = instructor_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.git_server_id = git_server_id
        self.git_staging_server_id = git_staging_server_id
        
    def __repr__(self):
        return "<Instructor %s: %s>" % (self.id, self.get_full_name())        
        
    def get_full_name(self, comma = False):
        if comma:
            return "%s, %s" % (self.last_name, self.first_name)
        else:
            return "%s %s" % (self.first_name, self.last_name)    

        
class Team(object):
    def __init__(self, team_id):
        self.id = team_id
        
        self.private_name = None

        self.students = []
        self.active = True
        self.git_repo_created = False
        self.git_staging_repo_created = False
        
        self.projects = {}

    def __repr__(self):
        return "<Team %s>" % self.id
        
    def add_student(self, student):
        self.students.append(student)
        
    def get_project(self, project_id):
        return self.projects.get(project_id)
        
    def add_project(self, project):
        self.projects[project.id] = TeamProject(project)
        
    def has_project(self, project_id):
        return self.projects.has_key(project_id)
        
    def set_project_grade(self, project_id, grade_component, points):
        assert(isinstance(grade_component, GradeComponent))

        team_project = self.get_project(project_id)
        if team_project is None:
            raise ChisubmitModelException("Tried to assign grade, but team %s has not been assigned project %s" % (self.id, project_id)) 

        project = team_project.project

        if grade_component not in project.grade_components:
            raise ChisubmitModelException("Tried to assign grade, but project %s does not have grade component %s" % (project.id, grade_component.name))

        team_project.set_grade(grade_component, points)
        
class TeamProject(object):
    def __init__(self, project):
        self.project = project
        
        self.grader = None
        self.extensions_used = 0
        self.grades = {}
        self.penalties = []
        
    def __repr__(self):
        return "<TeamProject %s>" % (self.project.id)        
        
    def set_grade(self, grade_component, points):
        assert(isinstance(grade_component, GradeComponent))
        
        if points < 0 or points > grade_component.points:
            raise ChisubmitModelException("Tried to assign invalid number of points in '%s' (got %.2f, expected 0 <= x <= %.2f)" %
                                          (grade_component.name, points, grade_component.points))        
        
        self.grades[grade_component] = points
    
    def add_penalty(self, description, points):
        if points >= 0 :
            raise ChisubmitModelException("Tried to assign a non-negative penalty (%i points: %s)" %
                                          (points, description))    
        self.penalties.append( (description, points) )    

    def get_total_penalties(self):
        return sum([p for _, p in self.penalties])
        
    def get_total_grade(self):
        points = sum([p for p in self.grades.values()])
                
        return points + self.get_total_penalties()
        
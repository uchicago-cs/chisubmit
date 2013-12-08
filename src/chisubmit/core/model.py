import yaml
import math
import os.path
import chisubmit.core
from chisubmit.common.utils import set_datetime_timezone_local

class Course(object):
    def __init__(self, course_id, name, extensions):
        self.id = course_id
        self.name = name
        self.extensions = extensions
        
        self.github_organization = None
        self.github_instructors_team = None
        
        self.students = {}
        self.projects = {}
        self.teams = {}
        
        self.course_file = None
        
    def save(self, course_file = None):
        if self.course_file is None and course_file is None:
            raise Exception("Course object has no file associated with it")

        if course_file is None:
            course_file = self.course_file
            
        f = open(course_file, 'w')
        yaml.dump(self, f)
        f.close()
        
    @staticmethod
    def from_file(course_file):
        course = yaml.load(course_file)
        course.course_file = course_file.name
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
        
    def add_student(self, student):
        self.students[student.id] = student

    def add_project(self, project):
        self.projects[project.id] = project

    def add_team(self, team):
        self.teams[team.id] = team
        
    def get_team_gh_repo_url(self, team_id):
        team = self.teams[team_id]
        
        return "git@github.com:%s/%s.git" % (self.github_organization, team.github_repo)       

        
class GradeComponent(object):
    def __init__(self, name, points):
        self.name = name
        self.points = points        


class Project(object):
    def __init__(self, project_id, name, deadline):
        self.id = project_id
        self.name = name
        self.deadline = deadline
        self.grade_components = []
        
    def add_grade_component(self, grade_component):
        self.grade_components.append(grade_component)

    # We need to do this because PyYAML doesn't load
    # timezone data when reading dates. 
    # TODO: Just store everything in UTC       
    def get_deadline(self):
        return set_datetime_timezone_local(self.deadline)
        
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
    def __init__(self, student_id, first_name, last_name, email, github_id):
        self.id = student_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.github_id = github_id
        
        self.dropped = False
        
   
class Grader(object):
    def __init__(self, student_id, first_name, last_name, email, github_id):
        self.id = student_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.github_id = github_id
                   
        
class Team(object):
    def __init__(self, team_id):
        self.id = team_id

        self.students = []
        self.active = True
        self.github_repo = None
        self.github_team = None
        
        self.projects = {}
        
    def add_student(self, student):
        self.students.append(student)
        
    def add_project(self, project):
        self.projects[project.id] = TeamProject(project)
        
        
class TeamProject(object):
    def __init__(self, project):
        self.project = project
        
        self.grader = None
        self.extensions_used = 0
        self.grades = {}
        
    def set_grade(self, grade_component, points):
        self.grades[grade_component] = points
    
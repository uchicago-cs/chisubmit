import yaml


class Course(object):
    def __init__(self, course_id, name, extensions):
        self.id = course_id
        self.name = name
        self.extensions = extensions
        
        self.students = {}
        self.projects = {}
        self.teams = {}
        
    def to_file(self, course_file):
        yaml.dump(self, course_file)
        
    @staticmethod
    def from_file(course_file):
        return yaml.load(course_file)
        
    def add_student(self, student):
        self.students[student.id] = student

    def add_project(self, project):
        self.projects[project.id] = project

    def add_team(self, team):
        self.teams[team.id] = team
        
        
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
    
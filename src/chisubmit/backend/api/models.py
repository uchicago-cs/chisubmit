from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from enum import Enum
from django.db.utils import IntegrityError
from chisubmit.common.utils import compute_extensions_needed,\
    is_submission_ready_for_grading
from rest_framework.response import Response
from rest_framework import status
import jsonfield

class CourseRoles(Enum):
    ADMIN = 0
    INSTRUCTOR = 1
    GRADER = 2
    STUDENT = 3

GradersAndStudents = set([CourseRoles.GRADER, CourseRoles.STUDENT])
AllExceptAdmin = set([CourseRoles.INSTRUCTOR, CourseRoles.GRADER, CourseRoles.STUDENT])
Students = set([CourseRoles.STUDENT])

class OwnerPermissions(Enum):
    READ = 0
    WRITE = 1

Read = set([OwnerPermissions.READ])
Write = set([OwnerPermissions.WRITE])
ReadWrite = Read | Write

def get_user_by_username(username):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None    

class Course(models.Model):
    course_id = models.SlugField(unique = True)
    name = models.CharField(max_length=64)
    
    instructors = models.ManyToManyField(User, through='Instructor', related_name="instructor_in")
    graders = models.ManyToManyField(User, through='Grader', related_name="grader_in")
    students = models.ManyToManyField(User, through='Student', related_name="student_in")
    
    def __unicode__(self):
        return u"%s: %s" % (self.course_id, self.name)
    
    @classmethod
    def get_by_course_id(cls, course_id):
        try:
            return cls.objects.get(course_id=course_id)
        except cls.DoesNotExist:
            return None
            
    def has_instructor(self, user):
        return Instructor.objects.filter(course=self, user=user).exists()
    
    def get_instructor(self, user):
        try:
            return Instructor.objects.get(course=self, user=user)
        except Instructor.DoesNotExist:
            return None        

    def has_grader(self, user):
        return Grader.objects.filter(course=self, user=user).exists()

    def get_grader(self, user):
        try:
            return Grader.objects.get(course=self, user=user)
        except Grader.DoesNotExist:
            return None        

    def has_student(self, user):
        return Student.objects.filter(course=self, user=user).exists()
    
    def get_student(self, user):
        try:
            return Student.objects.get(course=self, user=user)
        except Student.DoesNotExist:
            return None        

    def has_user(self, user):
        return self.has_student(user) or self.has_instructor(user) or self.has_grader(user) 
    
    def has_access(self, user):
        return user.is_staff or user.is_superuser or self.has_user(user)
    
    def get_roles(self, user):
        roles = set()
        if self.has_instructor(user):
            roles.add(CourseRoles.INSTRUCTOR)
        if self.has_grader(user):
            roles.add(CourseRoles.GRADER)
        if self.has_student(user):
            roles.add(CourseRoles.STUDENT)
        if user.is_staff or user.is_superuser:
            roles.add(CourseRoles.ADMIN)
        return roles
    
    def get_assignment(self, assignment_id):
        try:
            return Assignment.objects.get(course__course_id=self.course_id, assignment_id=assignment_id)
        except Assignment.DoesNotExist:
            return None
        
    def get_team(self, team_id):
        try:
            return self.team_set.get(team_id=team_id)
        except Team.DoesNotExist:
            return None        

    def get_teams(self):
        return self.team_set.all()
        
    def get_teams_with_students(self, students):
        return self.team_set.filter(students__in = students).distinct()
    
    # OPTIONS
    GIT_USERNAME_USER = 'user-id'
    GIT_USERNAME_CUSTOM = 'custom'
    GIT_USERNAME_CHOICES = (
        (GIT_USERNAME_USER, 'Same as user id'),
        (GIT_USERNAME_CUSTOM, 'Custom git username'),
    )
    
    EXT_PER_TEAM = "per-team"
    EXT_PER_STUDENT = "per-student"
    EXT_CHOICES = (
        (EXT_PER_TEAM, 'Extensions per team'),
        (EXT_PER_STUDENT, 'Extensions per student'),
    )
    
    git_server_connstr = models.CharField(max_length=256, null=True)
    git_staging_connstr = models.CharField(max_length=256, null=True)
    git_usernames = models.CharField(max_length=16, choices=GIT_USERNAME_CHOICES, default=GIT_USERNAME_USER)
    git_staging_usernames = models.CharField(max_length=16, choices=GIT_USERNAME_CHOICES, default=GIT_USERNAME_USER)
    extension_policy = models.CharField(max_length=16, choices=EXT_CHOICES, default=EXT_PER_STUDENT)
    default_extensions = models.IntegerField(default=0, validators = [MinValueValidator(0)])    
    
class Instructor(models.Model):
    user = models.ForeignKey(User)
    course = models.ForeignKey(Course)
    
    git_username = models.CharField(max_length=64, null=True)
    git_staging_username = models.CharField(max_length=64, null=True)

    def __unicode__(self):
        return u"Instructor %s of %s" % (self.user.username, self.course.course_id) 

    class Meta:
        unique_together = ("user", "course")

class Grader(models.Model):
    user = models.ForeignKey(User)
    course = models.ForeignKey(Course)
    
    git_username = models.CharField(max_length=64)
    git_staging_username = models.CharField(max_length=64)
    
    conflicts = models.ManyToManyField("Student", blank=True)
    
    def __unicode__(self):
        return u"Grader %s of %s" % (self.user.username, self.course.course_id)     
    
    class Meta:
        unique_together = ("user", "course")    
    
class Student(models.Model):
    user = models.ForeignKey(User)
    course = models.ForeignKey(Course)
    
    git_username = models.CharField(max_length=64)
    
    extensions = models.IntegerField(default=0, validators = [MinValueValidator(0)])
    dropped = models.BooleanField(default = False)
    
    def __unicode__(self):
        return u"Student %s of %s" % (self.user.username, self.course.course_id)     
    
    def get_extensions_available(self):
        extensions_used = 0
        
        teams = self.course.get_teams_with_students([self])
        
        for team in teams:
            for registration in team.registration_set.all():
                if registration.final_submission is not None:
                    extensions_used += registration.final_submission.extensions_used

        return self.extensions - extensions_used    
    
    class Meta:
        unique_together = ("user", "course")    

class Assignment(models.Model):
    course = models.ForeignKey(Course)
    assignment_id = models.SlugField()
    name = models.CharField(max_length=64)
    deadline = models.DateTimeField()

    # Options
    min_students = models.IntegerField(default=1, validators = [MinValueValidator(1)])
    max_students = models.IntegerField(default=1, validators = [MinValueValidator(1)])  
            
    def __unicode__(self):
        return u"Assignment %s of %s" % (self.assignment_id, self.course.course_id)     

    def get_rubric_components(self):
        return list(RubricComponent.objects.filter(assignment=self))
    
    def get_rubric_component_by_id(self, rc_id):
        try:
            return RubricComponent.objects.get(pk = rc_id)
        except RubricComponent.DoesNotExist:
            return None

    def get_rubric_component_by_description(self, description):
        try:
            return RubricComponent.objects.get(assignment = self, description = description)
        except RubricComponent.DoesNotExist:
            return None

    class Meta:
        unique_together = ("assignment_id", "course")    

class RubricComponent(models.Model):    
    assignment = models.ForeignKey(Assignment)
    order = models.IntegerField(default=0, validators = [MinValueValidator(0)])
    description = models.CharField(max_length=64)
    points = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        unique_together = ("assignment", "description")
        ordering = ("assignment", "order")
        
        
class Team(models.Model):
    course = models.ForeignKey(Course)
    team_id = models.SlugField(max_length=128)
    extensions = models.IntegerField(default=0, validators = [MinValueValidator(0)])
    active = models.BooleanField(default = True)
    
    students = models.ManyToManyField(Student, through='TeamMember', related_name="team_member_in")
    
    registrations = models.ManyToManyField(Assignment, through='Registration') 
    
    def __unicode__(self):
        return u"Team %s in %s" % (self.team_id, self.course.course_id)         
    
    def is_registered_for_assignment(self, assignment):
        return self.registrations.filter(assignment_id = assignment.assignment_id).exists()
    
    def get_registrations(self):
        return self.registration_set.all()    
    
    def get_registration(self, assignment):
        try:
            return self.registration_set.get(assignment = assignment)
        except Registration.DoesNotExist:
            return None        

    def get_team_members(self):
        return self.teammember_set.all()
        
    def get_team_member(self, student):
        try:
            return self.teammember_set.get(student = student)
        except TeamMember.DoesNotExist:
            return None        
        
    def get_extensions_used(self):
        extensions = 0
        for r in self.registration_set.all():
            if r.final_submission is not None:
                extensions += r.final_submission.extensions_used
        return extensions 
        
    def get_extensions_available(self):
        if self.course.extension_policy == Course.EXT_PER_TEAM:
            return self.extensions - self.get_extensions_used()    
        elif self.course.extension_policy == Course.EXT_PER_STUDENT:
            student_extensions_available = []
            for student in self.students.all():
                a = student.get_extensions_available()
                student_extensions_available.append(a)
            return min(student_extensions_available)
        else:
            raise IntegrityError("course.extension_policy has invalid value: %s" % (self.course.extension_policy))          
    
    class Meta:
        unique_together = ("course", "team_id")
        
class TeamMember(models.Model):
    student = models.ForeignKey(Student)
    team = models.ForeignKey(Team)
    
    confirmed = models.BooleanField(default = False)
    
    class Meta:
        unique_together = ("student", "team")        
        
class Registration(models.Model):
    team = models.ForeignKey(Team)
    assignment = models.ForeignKey(Assignment)

    grader = models.ForeignKey(Grader, null=True)
    grade_adjustments = jsonfield.JSONField(blank=True, null=True)
    final_submission = models.ForeignKey("Submission", related_name="final_submission_of", null=True) 

    def is_ready_for_grading(self):
        if self.final_submission is None:
            return False
        else:
            return is_submission_ready_for_grading(assignment_deadline=self.assignment.deadline, 
                                                   submission_date=self.final_submission.submitted_at,
                                                   extensions_used=self.final_submission.extensions_used)

    class Meta:
        unique_together = ("team", "assignment")

class Submission(models.Model):
    registration = models.ForeignKey(Registration) 
    extensions_used = models.IntegerField(default=0, validators = [MinValueValidator(0)])
    commit_sha = models.CharField(max_length=40)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def validate(self):
        extensions_needed = compute_extensions_needed(submission_time = self.submitted_at, 
                                                      deadline = self.registration.assignment.deadline)
        extensions_available = self.registration.team.get_extensions_available()
                
        if extensions_available < 0:
            msg = "The number of available extensions is negative"
            return False, Response({"fatal": [msg]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR), None           

        if self.registration.final_submission is not None:
            extensions_used_in_existing_submission = self.registration.final_submission.extensions_used
        else:
            extensions_used_in_existing_submission = 0 
        
        error_data = {"extensions_available": extensions_available,
                      "extensions_requested": self.extensions_used,
                      "extensions_needed": extensions_needed,
                      "submitted_at": self.submitted_at.isoformat(sep=" "),
                      "deadline": self.registration.assignment.deadline.isoformat(sep=" ")}
        
        if self.extensions_used != extensions_needed:
            msg = "The number of requested extensions does not match the number of extensions needed."
            response_data = {"errors": [msg]}
            response_data.update(error_data)
            return False, Response(response_data, status=status.HTTP_400_BAD_REQUEST), None            
        
        if extensions_available + extensions_used_in_existing_submission < extensions_needed:
            msg = "The number of available extensions is insufficient."
            response_data = {"errors": [msg]}
            response_data.update(error_data)
            return False, Response(response_data, status=status.HTTP_400_BAD_REQUEST), None                    
        else:     
            extensions = {}
            extensions["extensions_available_before"] = extensions_available
            
            # If the team has already used extensions for a previous submission,
            # they don't count towards the number of extensions needed
            # They are 'credited' to the available extensions
            extensions_available += extensions_used_in_existing_submission
            
            extensions_available -= extensions_needed

            extensions["extensions_available_after"] = extensions_available
            
            return True, None, extensions                    
        
class Grade(models.Model):
    registration = models.ForeignKey(Registration)
    rubric_component = models.ForeignKey(RubricComponent)
    
    points = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        unique_together = ("registration", "rubric_component")    
    
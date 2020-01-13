from builtins import object
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from enum import Enum
from datetime import timedelta
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
    archived = models.BooleanField(default = False)    
    
    instructors = models.ManyToManyField(User, through='Instructor', related_name="instructor_in")
    graders = models.ManyToManyField(User, through='Grader', related_name="grader_in")
    students = models.ManyToManyField(User, through='Student', related_name="student_in")

    gradescope_id = models.IntegerField(null=True, blank=True)
    
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    git_username = models.CharField(max_length=64, null=True)
    git_staging_username = models.CharField(max_length=64, null=True)

    def __unicode__(self):
        return u"Instructor %s of %s" % (self.user.username, self.course.course_id) 

    class Meta(object):
        unique_together = ("user", "course")

class Grader(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    git_username = models.CharField(max_length=64)
    git_staging_username = models.CharField(max_length=64)
    
    conflicts = models.ManyToManyField("Student", blank=True)
    
    def __unicode__(self):
        return u"Grader %s of %s" % (self.user.username, self.course.course_id)     
    
    class Meta(object):
        unique_together = ("user", "course")    
    
class Student(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
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
    
    class Meta(object):
        unique_together = ("user", "course")    

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    assignment_id = models.SlugField()
    name = models.CharField(max_length=64)
    deadline = models.DateTimeField()
    grace_period = models.DurationField(default=timedelta(seconds=0))
    expected_files = models.TextField(null=True, blank=True)

    gradescope_id = models.IntegerField(null=True, blank=True)

    # Options
    min_students = models.IntegerField(default=1, validators = [MinValueValidator(1)])
    max_students = models.IntegerField(default=1, validators = [MinValueValidator(1)])  
            
    def __unicode__(self):
        return u"Assignment %s of %s" % (self.assignment_id, self.course.course_id)     

    def get_rubric_components(self):
        return list(RubricComponent.objects.filter(assignment=self).order_by("order"))
    
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

    class Meta(object):
        unique_together = ("assignment_id", "course")    

class RubricComponent(models.Model):    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    order = models.IntegerField(default=0, validators = [MinValueValidator(0)])
    description = models.CharField(max_length=64)
    points = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta(object):
        unique_together = ("assignment", "description")
        ordering = ("assignment", "order")
        
        
class Team(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
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
    
    class Meta(object):
        unique_together = ("course", "team_id")
        
class TeamMember(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    
    confirmed = models.BooleanField(default = False)
    
    class Meta(object):
        unique_together = ("student", "team")        
        
class Registration(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)

    grader = models.ForeignKey(Grader, null=True, on_delete=models.SET_NULL)
    grade_adjustments = jsonfield.JSONField(blank=True, null=True)
    final_submission = models.ForeignKey("Submission", related_name="final_submission_of", null=True, on_delete=models.SET_NULL)
    grading_started = models.BooleanField(default=False)
    gradescope_uploaded = models.BooleanField(default=False)

    def is_ready_for_grading(self):
        if self.final_submission is None:
            return False
        else:
            return is_submission_ready_for_grading(assignment_deadline=self.assignment.deadline, 
                                                   submission_date=self.final_submission.submitted_at,
                                                   extensions_used=self.final_submission.extensions_used,
                                                   assignment_grace_period=self.assignment.grace_period)

    class Meta(object):
        unique_together = ("team", "assignment")


class SubmissionValidationException(Exception):
    def __init__(self, error_response):
        Exception.__init__(self)
        self.error_response = error_response

class Submission(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE) 
    extensions_used = models.IntegerField(validators = [MinValueValidator(0)])
    commit_sha = models.CharField(max_length=40)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    in_grace_period = models.BooleanField(default=False)
    
    @classmethod
    def create(cls, registration, commit_sha, submitted_at, submitted_by, extensions_override):
        deadline = registration.assignment.deadline
        grace_period = registration.assignment.grace_period
        effective_deadline = deadline + grace_period
        
        extensions_needed = compute_extensions_needed(submission_time = submitted_at, 
                                                      deadline = effective_deadline)
        extensions_needed_without_grace_period = compute_extensions_needed(submission_time = submitted_at, 
                                                      deadline = deadline)
        
        if extensions_override is None and extensions_needed_without_grace_period == extensions_needed + 1:
            in_grace_period = True
        else:
            in_grace_period = False
        
        extensions_available = registration.team.get_extensions_available()
                
        if extensions_available < 0:
            msg = "The number of available extensions is negative"
            return False, Response({"fatal": [msg]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR), None           

        if registration.final_submission is not None:
            extensions_used_in_existing_submission = registration.final_submission.extensions_used
        else:
            extensions_used_in_existing_submission = 0 
        
        error_data = {"extensions_available": extensions_available,
                      "extensions_needed": extensions_needed,
                      "submitted_at": submitted_at.isoformat(sep=" "),
                      "deadline": registration.assignment.deadline.isoformat(sep=" ")}
        
        if extensions_override is None and extensions_available + extensions_used_in_existing_submission < extensions_needed:
            msg = "You do not have enough extensions to make this submission."
            response_data = {"errors": [msg]}
            response_data.update(error_data)
            response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            raise SubmissionValidationException(response)
        if extensions_override is not None and extensions_available + extensions_used_in_existing_submission - extensions_override < 0:
            msg = "The extensions override you have specified would leave the team with a negative number of extensions."
            error_data["extensions_override"] = extensions_override
            response_data = {"errors": [msg]}
            response_data.update(error_data)
            response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            raise SubmissionValidationException(response)
        else:     
            extensions = {}
            extensions["extensions_available_before"] = extensions_available
            
            # If the team has already used extensions for a previous submission,
            # they don't count towards the number of extensions needed
            # They are 'credited' to the available extensions
            extensions_available += extensions_used_in_existing_submission
            
            if extensions_override is not None:
                extensions["extensions_override"] = extensions_override
                extensions_used = extensions_override
            else:
                extensions_used = extensions_needed

            extensions_available -= extensions_used 

            extensions["extensions_available_after"] = extensions_available
            extensions["extensions_needed"] = extensions_needed            
            
            submission = cls(registration = registration,
                             extensions_used = extensions_used,
                             commit_sha = commit_sha,
                             submitted_at = submitted_at,
                             submitted_by = submitted_by,
                             in_grace_period = in_grace_period)
            
            return submission, extensions                    
        
class Grade(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    rubric_component = models.ForeignKey(RubricComponent, on_delete=models.CASCADE)
    
    points = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta(object):
        unique_together = ("registration", "rubric_component")    
    

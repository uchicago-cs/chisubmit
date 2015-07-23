from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from enum import Enum

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
        
    def get_team(self, team_name):
        try:
            return self.team_set.get(name=team_name)
        except Assignment.DoesNotExist:
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
    
    git_server_connstr = models.CharField(max_length=64, null=True)
    git_staging_connstr = models.CharField(max_length=64, null=True)
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
    name = models.SlugField(max_length=128)
    extensions = models.IntegerField(default=0, validators = [MinValueValidator(0)])
    active = models.BooleanField(default = True)
    
    students = models.ManyToManyField(Student, through='TeamMember', related_name="team_member_in")
    
    registrations = models.ManyToManyField(Assignment, through='Registration') 
    
    def __unicode__(self):
        return u"Team %s in %s" % (self.name, self.course.course_id)         
    
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
    
    class Meta:
        unique_together = ("course", "name")
        
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
    final_submission = models.ForeignKey("Submission", related_name="final_submission_of", null=True) 

    class Meta:
        unique_together = ("team", "assignment")

class Submission(models.Model):
    registration = models.ForeignKey(Registration) 
    extensions_used = models.IntegerField(default=0, validators = [MinValueValidator(0)])
    commit_sha = models.CharField(max_length=40)
    submitted_at = models.DateTimeField()
        
class Grade(models.Model):
    team = models.ForeignKey(Team)
    rubric_component = models.ForeignKey(RubricComponent)
    
    points = models.DecimalField(max_digits=5, decimal_places=2)
    
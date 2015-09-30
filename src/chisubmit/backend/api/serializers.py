from rest_framework import serializers
from chisubmit.backend.api.models import Course, GradersAndStudents, AllExceptAdmin,\
    Students, Student, Instructor, Grader, Team, Assignment, ReadWrite,\
    OwnerPermissions, Read, RubricComponent, TeamMember, Registration,\
    Submission, Grade
from django.contrib.auth.models import User
from rest_framework.reverse import reverse
from rest_framework.relations import RelatedField
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy

class ChisubmitSerializer(serializers.Serializer):
    
    def to_representation(self, obj):
        # TODO: Avoid generating the representation for fields that
        # aren't going to be returned anyways
        data = super(ChisubmitSerializer, self).to_representation(obj)

        course = self.context.get("course", None)
        request = self.context.get("request", None)
        if request is not None:
            user = request.user
        else:
            user = None

        if course is not None and user is not None:
            is_owner = self.context.get("is_owner", False)
            owner_override = getattr(self, "owner_override", {})
            
            if hasattr(self, "hidden_fields"):
                roles = self.context.get("roles", set())
                fields = data.keys()
                for f in fields:
                    if f in self.hidden_fields:
                        if not (is_owner and OwnerPermissions.READ in owner_override.get(f, [])):
                            if roles.issubset(self.hidden_fields[f]):
                                data.pop(f)
        
        return data
    
    def to_internal_value(self, data):
        internal_value = super(ChisubmitSerializer, self).to_internal_value(data)

        course = self.context.get("course", None)
        request = self.context.get("request", None)
        if request is not None:
            user = request.user
        else:
            user = None
        is_owner = self.context.get("is_owner", False)
        
        if course is not None and user is not None:
            roles = self.context.get("roles", set())
            fields = internal_value.keys()
            owner_override = getattr(self, "owner_override", {})

            for f in fields:
                if hasattr(self, "hidden_fields") and f in self.hidden_fields:
                    if not (is_owner and OwnerPermissions.READ in owner_override.get(f, [])):
                        if roles.issubset(self.hidden_fields[f]):
                            internal_value.pop(f)
                elif hasattr(self, "readonly_fields") and f in self.readonly_fields:
                    if not (is_owner and OwnerPermissions.WRITE in owner_override.get(f, [])):
                        if roles.issubset(self.readonly_fields[f]):
                            internal_value.pop(f)

        return internal_value
          
        
class UserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    email = serializers.EmailField() 
    
    def create(self, validated_data):
        return User.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance      
    

class CourseSerializer(ChisubmitSerializer):
    course_id = serializers.SlugField()
    name = serializers.CharField(max_length=64)
    
    url = serializers.SerializerMethodField()    
    instructors_url = serializers.SerializerMethodField()
    graders_url = serializers.SerializerMethodField()
    students_url = serializers.SerializerMethodField()
    assignments_url = serializers.SerializerMethodField()
    teams_url = serializers.SerializerMethodField()
    
    
    git_server_connstr = serializers.CharField(max_length=256, required=False)
    git_staging_connstr = serializers.CharField(max_length=256, required=False)
    git_usernames = serializers.ChoiceField(choices=Course.GIT_USERNAME_CHOICES, default=Course.GIT_USERNAME_USER)
    git_staging_usernames = serializers.ChoiceField(choices=Course.GIT_USERNAME_CHOICES, default=Course.GIT_USERNAME_USER)
    extension_policy = serializers.ChoiceField(choices=Course.EXT_CHOICES, default=Course.EXT_PER_STUDENT)
    default_extensions = serializers.IntegerField(default=0, min_value=0)    
    
    hidden_fields = { "git_staging_connstr": Students,    
                      "git_usernames": GradersAndStudents,
                      "git_staging_usernames": GradersAndStudents,
                      "extension_policy": GradersAndStudents,
                      "default_extensions": GradersAndStudents
                    }
    
    readonly_fields = { "course_id": AllExceptAdmin,
                        "name": AllExceptAdmin,
                        "git_server_connstr": AllExceptAdmin,
                        "git_staging_connstr": AllExceptAdmin,                        
                        "git_usernames": AllExceptAdmin,
                        "git_staging_usernames": AllExceptAdmin,
                        "extension_policy": AllExceptAdmin,
                        "default_extensions": AllExceptAdmin
                      }

    def get_url(self, obj):
        return reverse('course-detail', args=[obj.course_id], request=self.context["request"])

    def get_instructors_url(self, obj):
        return reverse('instructor-list', args=[obj.course_id], request=self.context["request"])    

    def get_graders_url(self, obj):
        return reverse('grader-list', args=[obj.course_id], request=self.context["request"])    
    
    def get_students_url(self, obj):
        return reverse('student-list', args=[obj.course_id], request=self.context["request"])    
    
    def get_assignments_url(self, obj):
        return reverse('assignment-list', args=[obj.course_id], request=self.context["request"])      

    def get_teams_url(self, obj):
        return reverse('team-list', args=[obj.course_id], request=self.context["request"])      
    
    def create(self, validated_data):
        return Course.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.course_id = validated_data.get('course_id', instance.course_id)
        instance.name = validated_data.get('name', instance.name)
        instance.git_server_connstr = validated_data.get('git_server_connstr', instance.git_server_connstr)
        instance.git_staging_connstr = validated_data.get('git_staging_connstr', instance.git_staging_connstr)
        instance.git_usernames = validated_data.get('git_usernames', instance.git_usernames)
        instance.git_staging_usernames = validated_data.get('git_staging_usernames', instance.git_staging_usernames)
        instance.extension_policy = validated_data.get('extension_policy', instance.extension_policy)
        instance.default_extensions = validated_data.get('default_extensions', instance.default_extensions)
        instance.save()
        return instance
    
    
class InstructorSerializer(ChisubmitSerializer):
    url = serializers.SerializerMethodField()
    username = serializers.SlugRelatedField(
        source="user",
        queryset=User.objects.all(),
        slug_field='username'
    )
    user = UserSerializer(read_only=True)
    git_username = serializers.CharField(max_length=64, required=False)
    git_staging_username = serializers.CharField(max_length=64, required=False)
    
    hidden_fields = { "git_username": AllExceptAdmin,
                      "git_staging_username": AllExceptAdmin }
    
    readonly_fields = { }
    
    owner_override = {"git_username": ReadWrite,
                      "git_staging_username": ReadWrite }
    
    def get_url(self, obj):
        return reverse('instructor-detail', args=[self.context["course"].course_id, obj.user.username], request=self.context["request"])
    
    def create(self, validated_data):
        return Instructor.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.git_username = validated_data.get('git_username', instance.git_username)
        instance.git_staging_username = validated_data.get('git_staging_username', instance.git_staging_username)
        instance.save()
        return instance    
    

class GraderSerializer(ChisubmitSerializer):
    url = serializers.SerializerMethodField()
    username = serializers.SlugRelatedField(
        source="user",
        queryset=User.objects.all(),
        slug_field='username'
    )
    user = UserSerializer(read_only=True)
    git_username = serializers.CharField(max_length=64, required=False)
    git_staging_username = serializers.CharField(max_length=64, required=False)
    
    hidden_fields = { "git_username": GradersAndStudents,
                      "git_staging_username": GradersAndStudents }
    
    readonly_fields = { }     
    
    owner_override = {"git_username": ReadWrite,
                      "git_staging_username": ReadWrite }    
    
    def get_url(self, obj):
        return reverse('grader-detail', args=[self.context["course"].course_id, obj.user.username], request=self.context["request"])
    
    def create(self, validated_data):
        return Grader.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.git_username = validated_data.get('git_username', instance.git_username)
        instance.git_staging_username = validated_data.get('git_staging_username', instance.git_staging_username)
        instance.save()
        return instance       
    
    
class StudentSerializer(ChisubmitSerializer):
    url = serializers.SerializerMethodField()
    username = serializers.SlugRelatedField(
        source="user",
        queryset=User.objects.all(),
        slug_field='username'
    )
    user = UserSerializer(read_only=True, required=False)
    git_username = serializers.CharField(max_length=64, required=False)
    
    extensions = serializers.IntegerField(min_value=0, required=False)
    dropped = serializers.BooleanField(default=False)
    
    hidden_fields = { "git_username": Students, 
                      "dropped": Students }
    
    readonly_fields = { "extensions": GradersAndStudents,
                        "dropped": GradersAndStudents
                      }     
    
    owner_override = { "git_username": ReadWrite }
        
    def get_url(self, obj):
        return reverse('student-detail', args=[self.context["course"].course_id, obj.user.username], request=self.context["request"])
    
    def create(self, validated_data):
        if not validated_data.has_key("extensions") and self.context["course"].extension_policy == "per-student":
            validated_data["extensions"] = self.context["course"].default_extensions
      
        return Student.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.git_username = validated_data.get('git_username', instance.git_username)
        instance.extensions = validated_data.get('extensions', instance.extensions)
        instance.dropped = validated_data.get('dropped', instance.dropped)
        instance.save()
        return instance    
    
    
    
class AssignmentSerializer(ChisubmitSerializer):
    assignment_id = serializers.SlugField()
    name = serializers.CharField(max_length=64)
    deadline = serializers.DateTimeField()
    
    url = serializers.SerializerMethodField()
    rubric_url = serializers.SerializerMethodField()
    
    min_students = serializers.IntegerField(default=1, min_value=1)
    max_students = serializers.IntegerField(default=1, min_value=1)
    
    readonly_fields = { "assignment_id": GradersAndStudents,
                        "name": GradersAndStudents,
                        "deadline": GradersAndStudents,
                        "min_students": GradersAndStudents,
                        "max_students": GradersAndStudents
                      }       
    
    def get_url(self, obj):
        return reverse('assignment-detail', args=[self.context["course"].course_id, obj.assignment_id], request=self.context["request"])

    def get_rubric_url(self, obj):
        return reverse('rubric-list', args=[self.context["course"].course_id, obj.assignment_id], request=self.context["request"])
    
    def create(self, validated_data):
        return Assignment.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.assignment_id = validated_data.get('assignment_id', instance.assignment_id)
        instance.name = validated_data.get('name', instance.name)
        instance.deadline = validated_data.get('deadline', instance.deadline)
        instance.min_students = validated_data.get('min_students', instance.min_students)
        instance.max_students = validated_data.get('max_students', instance.max_students)
        instance.save()
        return instance    
  

class RubricComponentSerializer(ChisubmitSerializer):
    id = serializers.IntegerField(read_only = True)
    order = serializers.IntegerField(default=1, min_value=1)
    description = serializers.CharField(max_length=64)
    points = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    url = serializers.SerializerMethodField()   
    
    readonly_fields = { "order": GradersAndStudents,
                        "description": GradersAndStudents,
                        "points": GradersAndStudents
                      }       
    
    def get_url(self, obj):
        return reverse('rubric-detail', args=[self.context["course"].course_id, obj.assignment.assignment_id, obj.pk], request=self.context["request"])
    
    def create(self, validated_data):
        return RubricComponent.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.order = validated_data.get('order', instance.order)
        instance.description = validated_data.get('description', instance.description)
        instance.points = validated_data.get('points', instance.points)
        instance.save()
        return instance

    
class TeamSerializer(ChisubmitSerializer):
    team_id = serializers.SlugField()
    extensions = serializers.IntegerField(default=0, min_value=0)
    active = serializers.BooleanField(default = True)
        
    url = serializers.SerializerMethodField()
    students_url = serializers.SerializerMethodField()
    assignments_url = serializers.SerializerMethodField()

    readonly_fields = { "active": GradersAndStudents,
                        "team_id": GradersAndStudents,
                        "extensions": GradersAndStudents
                      }       
    
    def get_url(self, obj):
        return reverse('team-detail', args=[self.context["course"].course_id, obj.team_id], request=self.context["request"])

    def get_students_url(self, obj):
        return reverse('teammember-list', args=[self.context["course"].course_id, obj.team_id], request=self.context["request"])

    def get_assignments_url(self, obj):
        return reverse('registration-list', args=[self.context["course"].course_id, obj.team_id], request=self.context["request"])
    
    def create(self, validated_data):
        return Team.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.team_id = validated_data.get('team_id', instance.team_id)
        instance.extensions = validated_data.get('extensions', instance.extensions)
        instance.active = validated_data.get('active', instance.min_students)
        instance.save()
        return instance         
    
class PersonRelatedField(RelatedField):
    default_error_messages = {
        'does_not_exist': ugettext_lazy('Object with username={value} does not exist.'),
        'invalid': ugettext_lazy('Invalid value.'),
    }
    
    def __init__(self, **kwargs):    
        super(PersonRelatedField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(user__username = data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return obj.user.username

    
class TeamMemberSerializer(ChisubmitSerializer):    
    url = serializers.SerializerMethodField()
    username = PersonRelatedField(source = "student",
                                  queryset=Student.objects.all()
                                  )
    student = StudentSerializer(read_only=True)
    confirmed = serializers.BooleanField(default=False)
    
    readonly_fields = { "confirmed": GradersAndStudents }        

    def __init__(self, *args, **kwargs):
        if kwargs.has_key("context"):        
            username_f = self.fields['username']
            username_f.queryset = username_f.queryset.filter(course = kwargs['context']['course'])

        super(TeamMemberSerializer, self).__init__(*args, **kwargs)

    def get_url(self, obj):
        return reverse('teammember-detail', args=[self.context["course"].course_id, obj.team.team_id, obj.student.user.username], request=self.context["request"])
    
    def create(self, validated_data):
        return TeamMember.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.confirmed = validated_data.get('confirmed', instance.confirmed)
        instance.save()
        return instance
    
class SubmissionSerializer(ChisubmitSerializer):    
    url = serializers.SerializerMethodField()
    id = serializers.IntegerField(read_only = True)
    extensions_used = serializers.IntegerField(default=0, min_value=0) 
    commit_sha = serializers.CharField(max_length=40)
    submitted_at = serializers.DateTimeField(required=False)
    
    readonly_fields = { 
                      "extensions_used": GradersAndStudents,
                      "commit_sha": GradersAndStudents,
                      "submitted_at": GradersAndStudents
                      }   

    def get_url(self, obj):
        if obj.pk is None:
            # If we do a dry-run submission, we will be seralizing a Submission object that has not
            # been saved, and thus doesn't have a primary key (or an endpoint)
            return None
        else:
            return reverse('submission-detail', args=[self.context["course"].course_id, obj.registration.team.team_id, obj.registration.assignment.assignment_id, obj.pk], request=self.context["request"])
    
    def create(self, validated_data):
        return Submission.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.extensions_used = validated_data.get('extensions_used', instance.extensions_used)
        instance.commit_sha = validated_data.get('commit_sha', instance.commit_sha)
        instance.submitted_at = validated_data.get('submitted_at', instance.submitted_at)
        instance.save()        
        return instance    
    
class RegistrationSerializer(ChisubmitSerializer):    
    url = serializers.SerializerMethodField()
    assignment_id = serializers.SlugRelatedField(
        source="assignment",
        queryset=Assignment.objects.all(),
        slug_field='assignment_id'
    )
    assignment = AssignmentSerializer(read_only=True, required=False) 
    grader_username = PersonRelatedField(
                                         source = "grader",
                                         queryset=Grader.objects.all(),
                                         required = False
                                         )
    grader = GraderSerializer(read_only=True, required=False)

    submissions_url = serializers.SerializerMethodField()
    final_submission_id = serializers.PrimaryKeyRelatedField(
        source="final_submission",
        queryset=Submission.objects.all(),
        required=False,
        allow_null=True
        )
    final_submission = SubmissionSerializer(read_only=True, required=False) 

    grades_url = serializers.SerializerMethodField()
    grade_adjustments = serializers.DictField(required=False,
                                              child=serializers.DecimalField(max_digits=5, decimal_places=2))

    readonly_fields = { "grade_adjustments": GradersAndStudents }

    hidden_fields = { 
                      "grader_username": Students,
                      "grader": Students                      
                    }   

    def __init__(self, *args, **kwargs):
        if kwargs.has_key("context"):   
            grader_username_f = self.fields['grader_username']
            grader_username_f.queryset = grader_username_f.queryset.filter(course = kwargs['context']['course'])

        super(RegistrationSerializer, self).__init__(*args, **kwargs)

    def get_url(self, obj):
        return reverse('registration-detail', args=[self.context["course"].course_id, obj.team.team_id, obj.assignment.assignment_id], request=self.context["request"])

    def get_submissions_url(self, obj):
        return reverse('submission-list', args=[self.context["course"].course_id, obj.team.team_id, obj.assignment.assignment_id], request=self.context["request"])

    def get_grades_url(self, obj):
        return reverse('grade-list', args=[self.context["course"].course_id, obj.team.team_id, obj.assignment.assignment_id], request=self.context["request"])
    
    def create(self, validated_data):
        return Registration.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.grader = validated_data.get('grader', instance.grader)
        instance.grade_adjustments = validated_data.get('grade_adjustments', instance.grade_adjustments)
        instance.final_submission = validated_data.get('final_submission', instance.final_submission)
        instance.save()
        return instance            
    

class RegistrationRequestSerializer(serializers.Serializer):
    students = serializers.ListField(
                                      child = serializers.CharField()
                                      )
    
class RegistrationResponseSerializer(serializers.Serializer):
    new_team = serializers.BooleanField()
    team = TeamSerializer()
    team_members = serializers.ListField(
                                         child = TeamMemberSerializer()
                                         )
    registration = RegistrationSerializer()    
    
class SubmissionRequestSerializer(serializers.Serializer):
    extensions = serializers.IntegerField(default=0, min_value=0) 
    commit_sha = serializers.CharField(max_length=40)
    ignore_deadline = serializers.BooleanField()

class SubmissionResponseSerializer(serializers.Serializer):
    submission = SubmissionSerializer()
    extensions_before = serializers.IntegerField() 
    extensions_after = serializers.IntegerField() 
    
class GradeSerializer(ChisubmitSerializer):
    rubric_component_id = serializers.PrimaryKeyRelatedField(
        source="rubric_component",
        queryset=RubricComponent.objects.all()
    )    
    rubric_component = RubricComponentSerializer(read_only=True)
    points = serializers.DecimalField(max_digits=5, decimal_places=2, required = False)
    
    url = serializers.SerializerMethodField()
        
    readonly_fields = { "points": GradersAndStudents }       
    
    def get_url(self, obj):
        return reverse('grade-detail', args=[self.context["course"].course_id, obj.registration.team.team_id, obj.registration.assignment.assignment_id, obj.pk], request=self.context["request"])
        
    def create(self, validated_data):
        return Grade.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.points = validated_data.get('points', instance.points)
        instance.save()
        return instance    
    
          
  
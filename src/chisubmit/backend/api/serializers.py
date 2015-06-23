from rest_framework import serializers
from chisubmit.backend.api.models import Course, GradersAndStudents, AllExceptAdmin,\
    Students, Student, Instructor, Grader, Team, Assignment
from django.contrib.auth.models import User
from rest_framework.reverse import reverse

class FieldPermissionsMixin(object):
    def get_filtered_data(self, course, user):
        data = dict(self.data)

        if hasattr(self, "hidden_fields"):
            roles = course.get_roles(user)
            fields = data.keys()
            for f in fields:
                if f in self.hidden_fields:
                    if roles.issubset(self.hidden_fields[f]):
                        data.pop(f)
        
        return data
        
    def filter_initial_data(self, course, user, raise_exception=False):
        roles = course.get_roles(user)
        fields = self.initial_data.keys()
        for f in fields:
            if hasattr(self, "hidden_fields") and f in self.hidden_fields:
                if roles.issubset(self.hidden_fields[f]):
                    self.initial_data.pop(f)
            elif hasattr(self, "readonly_fields") and  f in self.readonly_fields:
                if roles.issubset(self.readonly_fields[f]):
                    self.initial_data.pop(f)                
                
        
class UserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30, read_only=True)
    first_name = serializers.CharField(max_length=30, read_only=True)
    last_name = serializers.CharField(max_length=30, read_only=True)
    email = serializers.EmailField(read_only=True)    
    

class CourseSerializer(serializers.Serializer, FieldPermissionsMixin):
    shortname = serializers.SlugField()
    name = serializers.CharField(max_length=64)
    
    url = serializers.SerializerMethodField()    
    instructors_url = serializers.SerializerMethodField()
    graders_url = serializers.SerializerMethodField()
    students_url = serializers.SerializerMethodField()
    assignments_url = serializers.SerializerMethodField()
    teams_url = serializers.SerializerMethodField()
    
    
    git_usernames = serializers.ChoiceField(choices=Course.GIT_USERNAME_CHOICES, default=Course.GIT_USERNAME_USER)
    git_staging_usernames = serializers.ChoiceField(choices=Course.GIT_USERNAME_CHOICES, default=Course.GIT_USERNAME_USER)
    extension_policy = serializers.ChoiceField(choices=Course.EXT_CHOICES, default=Course.EXT_PER_STUDENT)
    default_extensions = serializers.IntegerField(default=0, min_value=0)    
    
    hidden_fields = { "git_usernames": GradersAndStudents,
                      "git_staging_usernames": GradersAndStudents,
                      "extension_policy": GradersAndStudents,
                      "default_extensions": GradersAndStudents
                    }
    
    readonly_fields = { "shortname": AllExceptAdmin,
                        "name": AllExceptAdmin,
                        "git_usernames": AllExceptAdmin,
                        "git_staging_usernames": AllExceptAdmin,
                        "extension_policy": AllExceptAdmin,
                        "default_extensions": AllExceptAdmin
                      }

    def get_url(self, obj):
        return reverse('course-detail', args=[obj.shortname], request=self.context["request"])

    def get_instructors_url(self, obj):
        return reverse('instructor-list', args=[obj.shortname], request=self.context["request"])    

    def get_graders_url(self, obj):
        return reverse('grader-list', args=[obj.shortname], request=self.context["request"])    
    
    def get_students_url(self, obj):
        return reverse('student-list', args=[obj.shortname], request=self.context["request"])    
    
    def get_assignments_url(self, obj):
        return reverse('assignment-list', args=[obj.shortname], request=self.context["request"])      

    def get_teams_url(self, obj):
        return reverse('team-list', args=[obj.shortname], request=self.context["request"])      
    
    def create(self, validated_data):
        return Course.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.shortname = validated_data.get('shortname', instance.shortname)
        instance.name = validated_data.get('name', instance.name)
        instance.git_usernames = validated_data.get('git_usernames', instance.git_usernames)
        instance.git_staging_usernames = validated_data.get('git_staging_usernames', instance.git_staging_usernames)
        instance.extension_policy = validated_data.get('extension_policy', instance.extension_policy)
        instance.default_extensions = validated_data.get('default_extensions', instance.default_extensions)
        instance.save()
        return instance
    
    
class InstructorSerializer(serializers.Serializer, FieldPermissionsMixin):
    url = serializers.SerializerMethodField()
    username = serializers.SlugRelatedField(
        source="user",
        queryset=User.objects.all(),
        slug_field='username'
    )
    user = UserSerializer(read_only=True)
    git_username = serializers.CharField(max_length=64)
    git_staging_username = serializers.CharField(max_length=64)
    
    hidden_fields = { "git_username": AllExceptAdmin,
                      "git_staging_username": AllExceptAdmin }
    
    readonly_fields = { }     
    
    def get_url(self, obj):
        return reverse('instructor-detail', args=[self.context["course"].shortname, obj.user.username], request=self.context["request"])
    
    def create(self, validated_data):
        return Instructor.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.git_username = validated_data.get('git_username', instance.git_username)
        instance.git_staging_username = validated_data.get('git_staging_username', instance.extensions)
        instance.save()
        return instance    
    

class GraderSerializer(serializers.Serializer, FieldPermissionsMixin):
    url = serializers.SerializerMethodField()
    username = serializers.SlugRelatedField(
        source="user",
        queryset=User.objects.all(),
        slug_field='username'
    )
    user = UserSerializer(read_only=True)
    git_username = serializers.CharField(max_length=64)
    git_staging_username = serializers.CharField(max_length=64)
    
    hidden_fields = { "git_username": AllExceptAdmin,
                      "git_staging_username": AllExceptAdmin }
    
    readonly_fields = { }     
    
    def get_url(self, obj):
        return reverse('grader-detail', args=[self.context["course"].shortname, obj.user.username], request=self.context["request"])
    
    def create(self, validated_data):
        return Grader.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.git_username = validated_data.get('git_username', instance.git_username)
        instance.git_staging_username = validated_data.get('git_staging_username', instance.extensions)
        instance.save()
        return instance       
    
    
class StudentSerializer(serializers.Serializer, FieldPermissionsMixin):
    url = serializers.SerializerMethodField()
    username = serializers.SlugRelatedField(
        source="user",
        queryset=User.objects.all(),
        slug_field='username'
    )
    user = UserSerializer(read_only=True)
    git_username = serializers.CharField(max_length=64)
    
    extensions = serializers.IntegerField()
    dropped = serializers.BooleanField()
    
    hidden_fields = { "dropped": Students }
    
    readonly_fields = { "extensions": GradersAndStudents,
                        "dropped": GradersAndStudents
                      }     
    
    def get_url(self, obj):
        return reverse('student-detail', args=[self.context["course"].shortname, obj.user.username], request=self.context["request"])
    
    def create(self, validated_data):
        return Student.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.git_username = validated_data.get('git_username', instance.git_username)
        instance.extensions = validated_data.get('extensions', instance.extensions)
        instance.dropped = validated_data.get('dropped', instance.dropped)
        instance.save()
        return instance    
    
    
    
class AssignmentSerializer(serializers.Serializer, FieldPermissionsMixin):
    shortname = serializers.SlugField()
    name = serializers.CharField(max_length=64)
    deadline = serializers.DateTimeField()
    
    url = serializers.SerializerMethodField()   
    
    min_students = serializers.IntegerField(default=1, min_value=1)
    max_students = serializers.IntegerField(default=1, min_value=1)
    
    readonly_fields = { "shortname": GradersAndStudents,
                        "name": GradersAndStudents,
                        "deadline": GradersAndStudents,
                        "min_students": GradersAndStudents,
                        "max_students": GradersAndStudents
                      }       
    
    def get_url(self, obj):
        return reverse('assignment-detail', args=[self.context["course"].shortname, obj.shortname], request=self.context["request"])
    
    def create(self, validated_data):
        return Assignment.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.shortname = validated_data.get('shortname', instance.shortname)
        instance.name = validated_data.get('name', instance.name)
        instance.deadline = validated_data.get('deadline', instance.deadline)
        instance.min_students = validated_data.get('min_students', instance.min_students)
        instance.max_students = validated_data.get('max_students', instance.max_students)
        instance.save()
        return instance    
    
    
class TeamSerializer(serializers.Serializer, FieldPermissionsMixin):
    name = serializers.SlugField()
    extensions = serializers.IntegerField(default=1, min_value=1)
    active = serializers.BooleanField()
        
    url = serializers.SerializerMethodField()   

    hidden_fields = { "active": Students }       
        
    readonly_fields = { "name": GradersAndStudents,
                        "extensions": GradersAndStudents
                      }       
    
    def get_url(self, obj):
        return reverse('team-detail', args=[self.context["course"].shortname, obj.name], request=self.context["request"])
    
    def create(self, validated_data):
        return Team.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.extensions = validated_data.get('extensions', instance.extensions)
        instance.active = validated_data.get('active', instance.min_students)
        instance.save()
        return instance         
    
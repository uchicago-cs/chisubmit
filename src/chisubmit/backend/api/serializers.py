from rest_framework import serializers
from chisubmit.backend.api.models import Course, GradersAndStudents, AllExceptAdmin

class FieldPermissionsMixin(object):
    def get_filtered_data(self, course, user):
        roles = course.get_roles(user)
        data = self.data
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
            if f in self.hidden_fields:
                if roles.issubset(self.hidden_fields[f]):
                    self.initial_data.pop(f)
            elif f in self.readonly_fields:
                if roles.issubset(self.readonly_fields[f]):
                    self.initial_data.pop(f)                
                
        

class CourseSerializer(serializers.Serializer, FieldPermissionsMixin):
    id = serializers.IntegerField(read_only=True)
    shortname = serializers.SlugField()
    name = serializers.CharField(max_length=64)
    
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
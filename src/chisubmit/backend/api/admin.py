from django.contrib import admin
import chisubmit.backend.api.models as models

admin.site.register(models.Course)
admin.site.register(models.Instructor)
admin.site.register(models.Grader)
admin.site.register(models.Student)
admin.site.register(models.Assignment)
admin.site.register(models.RubricComponent)
admin.site.register(models.Team)
admin.site.register(models.Registration)
admin.site.register(models.Submission)
admin.site.register(models.Grade)


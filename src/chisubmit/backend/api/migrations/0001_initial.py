# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('assignment_id', models.SlugField()),
                ('name', models.CharField(max_length=64)),
                ('deadline', models.DateTimeField()),
                ('min_students', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('max_students', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=64)),
                ('git_server_connstr', models.CharField(max_length=64, null=True)),
                ('git_staging_connstr', models.CharField(max_length=64, null=True)),
                ('git_usernames', models.CharField(default=b'user-id', max_length=16, choices=[(b'user-id', b'Same as user id'), (b'custom', b'Custom git username')])),
                ('git_staging_usernames', models.CharField(default=b'user-id', max_length=16, choices=[(b'user-id', b'Same as user id'), (b'custom', b'Custom git username')])),
                ('extension_policy', models.CharField(default=b'per-student', max_length=16, choices=[(b'per-team', b'Extensions per team'), (b'per-student', b'Extensions per student')])),
                ('default_extensions', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
            ],
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('points', models.DecimalField(max_digits=5, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='Grader',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('git_username', models.CharField(max_length=64)),
                ('git_staging_username', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Instructor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('git_username', models.CharField(max_length=64, null=True)),
                ('git_staging_username', models.CharField(max_length=64, null=True)),
                ('course', models.ForeignKey(to='api.Course')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('grade_adjustments', jsonfield.fields.JSONField(null=True, blank=True)),
                ('assignment', models.ForeignKey(to='api.Assignment')),
            ],
        ),
        migrations.CreateModel(
            name='RubricComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('description', models.CharField(max_length=64)),
                ('points', models.DecimalField(max_digits=5, decimal_places=2)),
                ('assignment', models.ForeignKey(to='api.Assignment')),
            ],
            options={
                'ordering': ('assignment', 'order'),
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('git_username', models.CharField(max_length=64)),
                ('extensions', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('dropped', models.BooleanField(default=False)),
                ('course', models.ForeignKey(to='api.Course')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extensions_used', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('commit_sha', models.CharField(max_length=40)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('registration', models.ForeignKey(to='api.Registration')),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('team_id', models.SlugField(max_length=128)),
                ('extensions', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('active', models.BooleanField(default=True)),
                ('course', models.ForeignKey(to='api.Course')),
                ('registrations', models.ManyToManyField(to='api.Assignment', through='api.Registration')),
            ],
        ),
        migrations.CreateModel(
            name='TeamMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('confirmed', models.BooleanField(default=False)),
                ('student', models.ForeignKey(to='api.Student')),
                ('team', models.ForeignKey(to='api.Team')),
            ],
        ),
        migrations.AddField(
            model_name='team',
            name='students',
            field=models.ManyToManyField(related_name='team_member_in', through='api.TeamMember', to='api.Student'),
        ),
        migrations.AddField(
            model_name='registration',
            name='final_submission',
            field=models.ForeignKey(related_name='final_submission_of', to='api.Submission', null=True),
        ),
        migrations.AddField(
            model_name='registration',
            name='grader',
            field=models.ForeignKey(to='api.Grader', null=True),
        ),
        migrations.AddField(
            model_name='registration',
            name='team',
            field=models.ForeignKey(to='api.Team'),
        ),
        migrations.AddField(
            model_name='grader',
            name='conflicts',
            field=models.ManyToManyField(to='api.Student', blank=True),
        ),
        migrations.AddField(
            model_name='grader',
            name='course',
            field=models.ForeignKey(to='api.Course'),
        ),
        migrations.AddField(
            model_name='grader',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='grade',
            name='registration',
            field=models.ForeignKey(to='api.Registration'),
        ),
        migrations.AddField(
            model_name='grade',
            name='rubric_component',
            field=models.ForeignKey(to='api.RubricComponent'),
        ),
        migrations.AddField(
            model_name='course',
            name='graders',
            field=models.ManyToManyField(related_name='grader_in', through='api.Grader', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='course',
            name='instructors',
            field=models.ManyToManyField(related_name='instructor_in', through='api.Instructor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='course',
            name='students',
            field=models.ManyToManyField(related_name='student_in', through='api.Student', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='assignment',
            name='course',
            field=models.ForeignKey(to='api.Course'),
        ),
        migrations.AlterUniqueTogether(
            name='teammember',
            unique_together=set([('student', 'team')]),
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together=set([('course', 'team_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='student',
            unique_together=set([('user', 'course')]),
        ),
        migrations.AlterUniqueTogether(
            name='rubriccomponent',
            unique_together=set([('assignment', 'description')]),
        ),
        migrations.AlterUniqueTogether(
            name='registration',
            unique_together=set([('team', 'assignment')]),
        ),
        migrations.AlterUniqueTogether(
            name='instructor',
            unique_together=set([('user', 'course')]),
        ),
        migrations.AlterUniqueTogether(
            name='grader',
            unique_together=set([('user', 'course')]),
        ),
        migrations.AlterUniqueTogether(
            name='grade',
            unique_together=set([('registration', 'rubric_component')]),
        ),
        migrations.AlterUniqueTogether(
            name='assignment',
            unique_together=set([('assignment_id', 'course')]),
        ),
    ]

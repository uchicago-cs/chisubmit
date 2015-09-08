from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from pprint import pprint
from chisubmit.backend.api.models import Course, Student, Instructor

class CourseTests(APITestCase):
    
    fixtures = ['users', 'course1', 'course1_users']
    
    def test_get_courses(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)
        
        url = reverse('course-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_get_course(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('course-detail', args=["cmsc40100"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_patch_course_as_admin(self):
        user = User.objects.get(username='admin')
        self.client.force_authenticate(user=user)

        url = reverse('course-detail', args=["cmsc40100"])
        response = self.client.patch(url, data={"name":"FOOBAR"})
        c = Course.objects.get(course_id='cmsc40100')
        self.assertEqual(c.name, "FOOBAR") 
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)   
        
    def test_patch_course_as_student(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('course-detail', args=["cmsc40100"])
        response = self.client.patch(url, data={"name":"FOOBAR"})
        c = Course.objects.get(course_id='cmsc40100')
        self.assertEqual(c.name, "Introduction to Software Testing") 
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_patch_course_instructor(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        url = reverse('instructor-detail', args=["cmsc40100", "instructor1"])
        response = self.client.patch(url, data={"git_username": "git-instructor1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)           

        instructor_obj = Instructor.objects.get(course__course_id = 'cmsc40100', user__username = "instructor1")
        self.assertEquals(instructor_obj.git_username, "git-instructor1")
        
        
    
        
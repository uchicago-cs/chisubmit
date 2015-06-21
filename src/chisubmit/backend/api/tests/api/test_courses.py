from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from pprint import pprint
from chisubmit.backend.api.models import Course

class CourseTests(APITestCase):
    
    fixtures = ['users', 'complete_course1']
    
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
        pprint(dict(response.data))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_patch_course_admin(self):
        user = User.objects.get(username='admin')
        self.client.force_authenticate(user=user)

        url = reverse('course-detail', args=["cmsc40100"])
        response = self.client.patch(url, data={"name":"FOOBAR"})
        c = Course.objects.get(shortname='cmsc40100')
        self.assertEqual(c.name, "FOOBAR") 
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)   
        
    def test_patch_course_student(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('course-detail', args=["cmsc40100"])
        response = self.client.patch(url, data={"name":"FOOBAR"})
        c = Course.objects.get(shortname='cmsc40100')
        self.assertEqual(c.name, "Introduction to Software Testing") 
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)   
    
        
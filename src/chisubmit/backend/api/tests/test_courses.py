from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

class CourseTests(APITestCase):
    
    fixtures = ['users', 'complete_course']
    
    def test_get_courses(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)
        
        url = reverse('course-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_get_course(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        url = reverse('course-detail', args=["cmsc40100"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)        
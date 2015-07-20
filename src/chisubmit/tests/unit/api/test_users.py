from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from pprint import pprint
from chisubmit.backend.api.models import Course

class UserTests(APITestCase):
    
    fixtures = ['users', 'complete_course1']
    
    def test_get_users(self):
        user = User.objects.get(username='admin')
        self.client.force_authenticate(user=user)
        
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_get_user(self):
        user = User.objects.get(username='admin')
        self.client.force_authenticate(user=user)

        url = reverse('user-detail', args=["instructor1"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_create_user(self):
        user = User.objects.get(username='admin')
        self.client.force_authenticate(user=user)

        url = reverse('user-list')
        
        post_data = {"username": "student100",
                     "first_name": "F_student100",
                     "last_name": "L_student100",
                     "email": "student100@example.org"}
        
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
        
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from pprint import pprint
from chisubmit.backend.api.models import Course

class TeamTests(APITestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams']
    
    def test_get_teams_as_admin(self):
        user = User.objects.get(username='admin')
        self.client.force_authenticate(user=user)
        
        url = reverse('team-list', args=["cmsc40100"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_teams_as_instructor(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)
        
        url = reverse('team-list', args=["cmsc40100"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_get_teams_as_student(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)
        
        url = reverse('team-list', args=["cmsc40100"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
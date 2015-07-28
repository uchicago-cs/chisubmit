from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User


class AssignmentTests(APITestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_pa1']
    
    def test_get_assignments(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)
        
        url = reverse('assignment-list', args=["cmsc40100"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_get_assignment(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('assignment-detail', args=["cmsc40100","pa1"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_create_assignment(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        url = reverse('assignment-list', args=["cmsc40100"])
        
        post_data = {"assignment_id": "pa3",
                     "name": "Programming Assignment 3",
                     "deadline": "2042-02-04 20:00:00+00:00"}
        
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
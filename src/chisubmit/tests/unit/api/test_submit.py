from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from chisubmit.common.utils import get_datetime_now_utc
from datetime import timedelta
from chisubmit.backend.api.models import Assignment

class SubmitTests(APITestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                         'course1_pa1', 'course1_pa1_registrations']  
        
    def test_correct_no_extensions(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('submit', args=["cmsc40100", "student1-student2", "pa1"])
        
        post_data = {
                     "commit_sha": "COMMITSHATEST",
                     "extensions": 0                     
                    }
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_correct_dry_run(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('submit', args=["cmsc40100", "student1-student2", "pa1"])
        
        post_data = {
                     "commit_sha": "COMMITSHATEST",
                     "extensions": 0                     
                    }
        response = self.client.post(url + "?dry_run=true", data = post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_incorrect_excessive_extensions(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('submit', args=["cmsc40100", "student1-student2", "pa1"])
        
        post_data = {
                     "commit_sha": "COMMITSHATEST",
                     "extensions": 1                     
                    }
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)           
        
    def test_correct_one_extension(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)
        
        deadline = get_datetime_now_utc() - timedelta(hours=23)
        assignment_obj = Assignment.objects.get(assignment_id = "pa1")
        assignment_obj.deadline = deadline
        assignment_obj.save()

        url = reverse('submit', args=["cmsc40100", "student1-student2", "pa1"])
        
        post_data = {
                     "commit_sha": "COMMITSHATEST",
                     "extensions": 1                   
                    }
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_incorrect_insufficient_extensions_requested(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)
        
        deadline = get_datetime_now_utc() - timedelta(hours=23)
        assignment_obj = Assignment.objects.get(assignment_id = "pa1")
        assignment_obj.deadline = deadline
        assignment_obj.save()

        url = reverse('submit', args=["cmsc40100", "student1-student2", "pa1"])
        
        post_data = {
                     "commit_sha": "COMMITSHATEST",
                     "extensions": 0                
                    }
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_incorrect_insufficient_extensions_in_team(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)
        
        deadline = get_datetime_now_utc() - timedelta(hours=23 + 24 + 24)
        assignment_obj = Assignment.objects.get(assignment_id = "pa1")
        assignment_obj.deadline = deadline
        assignment_obj.save()

        url = reverse('submit', args=["cmsc40100", "student1-student2", "pa1"])
        
        post_data = {
                     "commit_sha": "COMMITSHATEST",
                     "extensions": 3            
                    }
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)                 
        
class SubmitWithExistingSubmissionsTests(APITestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                         'course1_pa1', 'course1_pa1_registrations_with_submissions']
        
                
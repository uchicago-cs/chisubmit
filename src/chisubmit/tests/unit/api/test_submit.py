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
                    }
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["in_grace_period"], False)      
        self.assertEqual(response.data["submission"]["extensions_used"], 0)               
        self.assertEqual(response.data["extensions_before"], 2)
        self.assertEqual(response.data["extensions_after"], 2)
        
    def test_correct_no_extensions_grace_period(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        deadline = get_datetime_now_utc() - timedelta(minutes=10)
        assignment_obj = Assignment.objects.get(assignment_id = "pa1")
        assignment_obj.deadline = deadline
        assignment_obj.grace_period = timedelta(minutes=15)
        assignment_obj.save()

        url = reverse('submit', args=["cmsc40100", "student1-student2", "pa1"])
        
        post_data = {
                     "commit_sha": "COMMITSHATEST",
                    }
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["in_grace_period"], True)
        self.assertEqual(response.data["submission"]["extensions_used"], 0)               
        self.assertEqual(response.data["extensions_before"], 2)
        self.assertEqual(response.data["extensions_after"], 2)
        
    def test_correct_dry_run(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('submit', args=["cmsc40100", "student1-student2", "pa1"])
        
        post_data = {
                     "commit_sha": "COMMITSHATEST",
                    }
        response = self.client.post(url + "?dry_run=true", data = post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["in_grace_period"], False)
        self.assertEqual(response.data["submission"]["extensions_used"], 0)                 
        
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
        self.assertEqual(response.data["in_grace_period"], False)    
        self.assertEqual(response.data["submission"]["extensions_used"], 1) 
        self.assertEqual(response.data["extensions_before"], 2)
        self.assertEqual(response.data["extensions_after"], 1)
        
    def test_correct_one_extension_grace_period(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)
        
        deadline = get_datetime_now_utc() - timedelta(hours=24, minutes=10)
        assignment_obj = Assignment.objects.get(assignment_id = "pa1")
        assignment_obj.deadline = deadline
        assignment_obj.grace_period = timedelta(minutes=15)        
        assignment_obj.save()

        url = reverse('submit', args=["cmsc40100", "student1-student2", "pa1"])
        
        post_data = {
                     "commit_sha": "COMMITSHATEST",
                    }
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["in_grace_period"], True)
        self.assertEqual(response.data["submission"]["extensions_used"], 1)
        self.assertEqual(response.data["extensions_before"], 2)
        self.assertEqual(response.data["extensions_after"], 1)
        
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
                    }
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_incorrect_insufficient_extensions_in_team_extensions_override(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)
        
        deadline = get_datetime_now_utc() - timedelta(hours=23 + 24 + 24)
        assignment_obj = Assignment.objects.get(assignment_id = "pa1")
        assignment_obj.deadline = deadline
        assignment_obj.save()

        url = reverse('submit', args=["cmsc40100", "student1-student2", "pa1"])
        
        post_data = {
                     "commit_sha": "COMMITSHATEST",
                     "extensions_override": 2            
                    }
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["in_grace_period"], False)
        self.assertEqual(response.data["submission"]["extensions_used"], 2)                           
        self.assertEqual(response.data["extensions_override"], 2)        
        self.assertEqual(response.data["extensions_before"], 2)
        self.assertEqual(response.data["extensions_after"], 0)
        
class SubmitWithExistingSubmissionsTests(APITestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                         'course1_pa1', 'course1_pa1_registrations_with_submissions']
        
                
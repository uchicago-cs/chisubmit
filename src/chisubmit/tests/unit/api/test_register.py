from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

class RegisterTests(APITestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_pa1']
        
    def test_register_single_student(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('register', args=["cmsc40100", "pa1"])
        
        post_data = {"students": ["student1", "student2"]}
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_register_full_team(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('register', args=["cmsc40100", "pa1"])
        
        post_data = {"students": ["student1", "student2"]}
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)        

        user = User.objects.get(username='student2')
        self.client.force_authenticate(user=user)

        post_data = {"students": ["student1", "student2"]}
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_register_full_team_redundant(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('register', args=["cmsc40100", "pa1"])
        
        post_data = {"students": ["student1", "student2"]}
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)        

        user = User.objects.get(username='student2')
        self.client.force_authenticate(user=user)

        post_data = {"students": ["student1", "student2"]}
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('register', args=["cmsc40100", "pa1"])
        
        post_data = {"students": ["student1", "student2"]}
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)        
                
    def test_register_non_student(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        url = reverse('register', args=["cmsc40100", "pa1"])
        
        post_data = {"students": ["student1", "student2"]}
        
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        
class RegisterErrorTests(APITestCase):        
        
    fixtures = ['users', 'course1', 'course1_users', 'course1_pa1']
                
    def test_register_other_students(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('register', args=["cmsc40100", "pa1"])
        
        post_data = {"students": ["student2", "student3"]}
        
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_register_student_in_other_class(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('register', args=["cmsc40100", "pa1"])
        
        post_data = {"students": ["student1", "student5"]}
        
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)        
        
    def test_register_wrong_number_of_students(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('register', args=["cmsc40100", "pa1"])
        
        post_data = {"students": ["student1", "student2", "student3"]}
        
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)          
           
class RegisterExistingTeamErrorTests(APITestCase):             
                
    fixtures = ['users', 'course1', 'course1_users', 'course1_pa1', 'course1_teams']
    
    def test_register_in_different_groups(self):
        user = User.objects.get(username='student1')
        self.client.force_authenticate(user=user)

        url = reverse('register', args=["cmsc40100", "pa1"])
        
        post_data = {"students": ["student1", "student2"]}
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)          
        
        user = User.objects.get(username='student2')
        self.client.force_authenticate(user=user)

        post_data = {"students": ["student2", "student3"]}
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)     
             
                
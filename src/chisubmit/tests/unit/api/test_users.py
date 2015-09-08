from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from pprint import pprint
from chisubmit.backend.api.models import Course
import base64
from rest_framework.authtoken.models import Token

class UserTests(APITestCase):
    
    fixtures = ['users', 'course1', 'course1_users']
    
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
        
class UserTokenTests(APITestCase):        
        
    fixtures = ['users']        
        
    def test_get_token_admin(self):
        user = User.objects.get(username='admin')
        self.client.force_authenticate(user=user)

        url = reverse('user-token', args=['instructor1'])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_get_token_instructor(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        url = reverse('user-token', args=['instructor1'])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  
        
    def test_get_token_reset(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        url = reverse('user-token', args=['instructor1'])
        
        response = self.client.get(url + "?reset=true")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_get_token_instructor_auth(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        url = reverse('auth-user-token')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  
        
    def test_create_token_instructor_auth(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        token = Token.objects.get(user__username="instructor1")
        self.assertEqual(token.key, "instructor1token")    
        token.delete()

        url = reverse('auth-user-token')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)          
        
    def test_get_token_reset_auth(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        url = reverse('auth-user-token')
        
        response = self.client.get(url + "?reset=true")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)        
        
    def test_get_token_other_user(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        url = reverse('user-token', args=['instructor2'])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_get_token_basic_auth_ok(self):
        url = reverse('auth-user-token')
        
        response = self.client.get(url, HTTP_AUTHORIZATION = 'Basic ' + base64.b64encode('instructor1:instructor1'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)                
    
    def test_get_token_basic_auth_denied(self):
        url = reverse('auth-user-token')
        
        response = self.client.get(url, HTTP_AUTHORIZATION = 'Basic ' + base64.b64encode('instructor1:foobar'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)                
        
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User


class GradeTests(APITestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                         'course1_pa1', 'course1_pa1_registrations']    
            
    def test_create_grade(self):
        user = User.objects.get(username='instructor1')
        self.client.force_authenticate(user=user)

        url = reverse('grade-list', args=["cmsc40100","student1-student2","pa1"])
        
        post_data = {"rubric_component_id": 1,
                     "points": 30}
        
        response = self.client.post(url, data = post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
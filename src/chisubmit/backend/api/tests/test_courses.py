from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class CourseTests(APITestCase):
    
    fixtures = ['users', 'complete_course']
    
    def test_get_courses(self):
        url = reverse('course-list')
        response = self.client.get(url)
        print response.data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
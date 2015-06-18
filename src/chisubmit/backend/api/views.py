from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chisubmit.backend.api.models import Course
from chisubmit.backend.api.serializers import CourseSerializer

class CourseList(APIView):
    def get(self, request, format=None):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class CourseDetail(APIView):
    def get_object(self, course_slug):
        try:
            return Course.objects.get(shortname=course_slug)
        except Course.DoesNotExist:
            raise Http404
            
    def get(self, request, course_slug, format=None):
        course = self.get_object(course_slug)
        serializer = CourseSerializer(course)
        return Response(serializer.data)

    def put(self, request, course_slug, format=None):
        course = self.get_object(course_slug)
        serializer = CourseSerializer(course, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_slug, format=None):
        course = self.get_object(course_slug)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
                
 
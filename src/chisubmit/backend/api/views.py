from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chisubmit.backend.api.models import Course
from chisubmit.backend.api.serializers import CourseSerializer
from rest_framework.exceptions import PermissionDenied

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

class CourseQualifiedAPIView(APIView):
    def dispatch(self, request, *args, **kwargs):
        """
        We override `.dispatch()` to be able to check course-based permissions
        in a single place, instead of in every single view.
        """
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        
        try:
            if kwargs.has_key("course_slug"):
                course_slug = kwargs.pop("course_slug")
                try:
                    course = Course.objects.get(shortname=course_slug)
                except Course.DoesNotExist:
                    raise Http404                           
            else:
                # Should not happen unless there's an error in urls.py
                raise
            
            if not (request.user.is_staff or request.user.is_superuser or course.has_user(request.user)):
                raise PermissionDenied
            
            self.initial(request, *args, **kwargs)

            # Get the appropriate handler method
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(),
                                  self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            response = handler(request, course, *args, **kwargs)

        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response
    
class CourseDetail(CourseQualifiedAPIView):
            
    def get(self, request, course, format=None):
        serializer = CourseSerializer(course)
        data = serializer.get_filtered_data(course, request.user)
        return Response(data)

    def patch(self, request, course, format=None):
        serializer = CourseSerializer(course, data=request.data, partial=True)
        serializer.filter_initial_data(course, request.user)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, format=None):
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
                
 
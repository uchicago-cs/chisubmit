from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chisubmit.backend.api.models import Course, Student, Instructor, Grader,\
    Assignment, Team
from chisubmit.backend.api.serializers import CourseSerializer,\
    StudentSerializer, InstructorSerializer, GraderSerializer,\
    AssignmentSerializer, TeamSerializer
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User

class CourseList(APIView):
    def get(self, request, format=None):
        courses = Course.objects.all()
        if not (request.user.is_staff or request.user.is_superuser):
            courses = [c for c in courses if c.has_user(request.user)]
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, format=None):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied
        serializer = CourseSerializer(data=request.data, context={'request': request})
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
            if kwargs.has_key("course"):
                course_shortname = kwargs.pop("course")
                try:
                    course = Course.objects.get(shortname=course_shortname)
                except Course.DoesNotExist:
                    raise Http404                           
            else:
                # Should not happen unless there's an error in urls.py
                raise
            
            if not (request.user.is_staff or request.user.is_superuser or course.has_user(request.user)):
                raise Http404
            
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
        serializer = CourseSerializer(course, context={'request': request})
        data = serializer.get_filtered_data(course, request.user)
        return Response(data)

    def patch(self, request, course, format=None):
        serializer = CourseSerializer(course, data=request.data, partial=True, context={'request': request})
        serializer.filter_initial_data(course, request.user)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, format=None):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied
        
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
                
 
class PersonList(CourseQualifiedAPIView):
    def get(self, request, course, format=None):
        students = self.person_class.objects.filter(course = course.pk)
        serializer = self.person_serializer(students, many=True, context={'request': request, 'course': course})
        return Response(serializer.data)

    def post(self, request, course, format=None):
        serializer = self.person_serializer(data=request.data, context={'request': request, 'course': course})
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            if self.person_class.objects.filter(course=course, user=user).exists():
                return Response({"username": ["%s is already a %s in %s" % (user.username, self.person_str, course.shortname)]}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PersonDetail(CourseQualifiedAPIView):
            
    def get_person(self, course, username):
        try:
            user = User.objects.get(username = username)
            person = self.person_class.objects.get(course = course, user = user)
            return person
        except User.DoesNotExist:
            raise Http404  
        except self.person_class.DoesNotExist:
            raise Http404  
            
    def get(self, request, course, username, format=None):
        person = self.get_person(course, username)
        serializer = self.person_serializer(person, context={'request': request, 'course': course})
        return Response(serializer.data)

    def patch(self, request, course, username, format=None):
        person = self.get_person(course, username)
        serializer = self.person_serializer(person, data=request.data, partial=True, context={'request': request, 'course': course})        
        serializer.filter_initial_data(course, request.user)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, username, format=None):
        person = self.get_person(course, username)
        person.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    
    

class InstructorList(PersonList):
    person_class = Instructor    
    person_serializer = InstructorSerializer
    person_str = "instructor"
    
class InstructorDetail(PersonDetail):
    person_class = Instructor    
    person_serializer = InstructorSerializer
    person_str = "instructor"    
    

class GraderList(PersonList):
    person_class = Grader    
    person_serializer = GraderSerializer
    person_str = "grader"
    
class GraderDetail(PersonDetail):
    person_class = Grader    
    person_serializer = GraderSerializer
    person_str = "grader"    
        
        
class StudentList(PersonList):
    person_class = Student    
    person_serializer = StudentSerializer
    person_str = "student"
    
class StudentDetail(PersonDetail):
    person_class = Student    
    person_serializer = StudentSerializer
    person_str = "student"    
    
    
class AssignmentList(CourseQualifiedAPIView):
    def get(self, request, course, format=None):
        assignments = Assignment.objects.filter(course = course.pk)
        serializer = AssignmentSerializer(assignments, many=True, context={'request': request, 'course': course})
        return Response(serializer.data)

    def post(self, request, course, format=None):
        serializer = AssignmentSerializer(data=request.data, context={'request': request, 'course': course})
        if serializer.is_valid():
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    
class AssignmentDetail(CourseQualifiedAPIView):
            
    def get_assignment(self, course, assignment):
        try:
            assignment = Assignment.objects.get(course = course, shortname = assignment)
            return assignment
        except Assignment.DoesNotExist:
            raise Http404  

    def get(self, request, course, assignment, format=None):
        assignment_obj = self.get_assignment(course, assignment)
        serializer = AssignmentSerializer(assignment_obj, context={'request': request, 'course': course})
        return Response(serializer.data)

    def patch(self, request, course, assignment, format=None):
        assignment_obj = self.get_assignment(course, assignment)
        serializer = AssignmentSerializer(assignment_obj, data=request.data, partial=True, context={'request': request, 'course': course})        
        serializer.filter_initial_data(course, request.user)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, assignment, format=None):
        assignment_obj = self.get_assignment(course, assignment)
        assignment_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    
    
    
class TeamList(CourseQualifiedAPIView):
    def get(self, request, course, format=None):
        teams = Team.objects.filter(course = course.pk)
        serializer = TeamSerializer(teams, many=True, context={'request': request, 'course': course})
        return Response(serializer.data)

    def post(self, request, course, format=None):
        serializer = TeamSerializer(data=request.data, context={'request': request, 'course': course})
        if serializer.is_valid():
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        
    
    
class TeamDetail(CourseQualifiedAPIView):
            
    def get_team(self, course, team):
        try:
            team_obj = Assignment.objects.get(course = course, name = team)
            return team_obj
        except Assignment.DoesNotExist:
            raise Http404  

    def get(self, request, course, team, format=None):
        team_obj = self.get_team(course, team)
        serializer = TeamSerializer(team_obj, context={'request': request, 'course': course})
        return Response(serializer.data)

    def patch(self, request, course, team, format=None):
        team_obj = self.get_team(course, team)
        serializer = TeamSerializer(team_obj, data=request.data, partial=True, context={'request': request, 'course': course})        
        serializer.filter_initial_data(course, request.user)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, team, format=None):
        team_obj = self.get_team(course, team)
        team_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)        
    
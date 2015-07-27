from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chisubmit.backend.api.models import Course, Student, Instructor, Grader,\
    Assignment, Team, RubricComponent, get_user_by_username, TeamMember,\
    Registration, Submission, Grade
from chisubmit.backend.api.serializers import CourseSerializer,\
    StudentSerializer, InstructorSerializer, GraderSerializer,\
    AssignmentSerializer, TeamSerializer, UserSerializer,\
    RubricComponentSerializer, RegistrationRequestSerializer, RegistrationSerializer, TeamMemberSerializer,\
    RegistrationResponseSerializer, SubmissionSerializer,\
    SubmissionRequestSerializer, SubmissionResponseSerializer, GradeSerializer
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.db import Error
from rest_framework.authentication import BasicAuthentication,\
    TokenAuthentication
from rest_framework.authtoken.models import Token
from twisted.protocols.ftp import PermissionDeniedError
from chisubmit.common.utils import get_datetime_now_utc,\
    compute_extensions_needed

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
            course_id = serializer.validated_data["course_id"]
            if Course.get_by_course_id(course_id) is not None:
                msg = "There is already a course with course_id = %s" % course_id
                return Response({"course_id": [msg]}, status=status.HTTP_400_BAD_REQUEST)
            try:
                serializer.save()
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
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
                course_id = kwargs.pop("course")
                try:
                    course = Course.objects.get(course_id=course_id)
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
        serializer = CourseSerializer(course, context={'request': request, 'course': course})
        
        return Response(serializer.data)

    def patch(self, request, course, format=None):
        serializer = CourseSerializer(course, data=request.data, partial=True, context={'request': request, 'course': course})
        
        if serializer.is_valid():
            try:
                serializer.save()
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
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
                return Response({"username": ["%s is already a %s in %s" % (user.username, self.person_str, course.course_id)]}, status=status.HTTP_400_BAD_REQUEST)

            try:
                serializer.save(course=course)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            
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
        is_owner = (request.user.username == username)
        serializer = self.person_serializer(person, data=request.data, partial=True, context={'request': request, 'course': course, 'is_owner': is_owner})        

        if serializer.is_valid():
            try:
                serializer.save()
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, username, format=None):
        if not (request.user.is_staff or request.user.is_superuser or course.has_instructor(request.user)):
            raise PermissionDenied        
        
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
            assignment_id = serializer.validated_data["assignment_id"]
            if course.get_assignment(assignment_id) is not None:
                msg = "There is already an assignment in course %s with assignment_id = %s" % (course.course_id, assignment_id)
                return Response({"assignment_id": [msg]}, status=status.HTTP_400_BAD_REQUEST)   
            try:
                serializer.save(course=course)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    
class AssignmentDetail(CourseQualifiedAPIView):
            
    def get_assignment(self, course, assignment):
        try:
            assignment = Assignment.objects.get(course = course, assignment_id = assignment)
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

        if serializer.is_valid():
            try:
                serializer.save()
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, assignment, format=None):
        if not (request.user.is_staff or request.user.is_superuser or course.has_instructor(request.user)):
            raise PermissionDenied        

        assignment_obj = self.get_assignment(course, assignment)
        assignment_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    
    
class RubricList(CourseQualifiedAPIView):
    def get_assignment(self, course, assignment):
        try:
            assignment = Assignment.objects.get(course = course, assignment_id = assignment)
            return assignment
        except Assignment.DoesNotExist:
            raise Http404      
    
    def get(self, request, course, assignment, format=None):
        assignment_obj = self.get_assignment(course, assignment)
        rubric_components = assignment_obj.get_rubric_components()
        serializer = RubricComponentSerializer(rubric_components, many=True, context={'request': request, 'course': course, 'assignment': assignment_obj})
        return Response(serializer.data)

    def post(self, request, course, assignment, format=None):
        assignment_obj = self.get_assignment(course, assignment)
        serializer = RubricComponentSerializer(data=request.data, context={'request': request, 'course': course, 'assignment': assignment_obj})
        if serializer.is_valid():
            description = serializer.validated_data["description"]
            rubric_description = assignment_obj.get_rubric_component_by_description(description)
            if rubric_description is not None:
                msg = "There is already a rubric component in assignment %s with description = '%s'" % (assignment, description)
                return Response({"description": [msg]}, status=status.HTTP_400_BAD_REQUEST)   
            try:
                serializer.save(assignment = assignment_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    
class RubricDetail(CourseQualifiedAPIView):
    def get_assignment(self, course, assignment):
        try:
            assignment = Assignment.objects.get(course = course, assignment_id = assignment)
            return assignment
        except Assignment.DoesNotExist:
            raise Http404   
            
    def get_rubric_component(self, assignment, rubric_component):
        try:
            return RubricComponent.objects.get(assignment=assignment, pk=rubric_component)
        except RubricComponent.DoesNotExist:
            raise Http404  

    def get(self, request, course, assignment, rubric_component, format=None):
        assignment_obj = self.get_assignment(course, assignment)
        rubric_component_obj = self.get_rubric_component(assignment_obj, rubric_component)
        serializer = RubricComponentSerializer(rubric_component_obj, context={'request': request, 'course': course})
        return Response(serializer.data)

    def patch(self, request, course, assignment, rubric_component, format=None):
        assignment_obj = self.get_assignment(course, assignment)
        rubric_component_obj = self.get_rubric_component(assignment_obj, rubric_component)
        serializer = RubricComponentSerializer(rubric_component_obj, data=request.data, partial=True, context={'request': request, 'course': course, 'assignment': assignment_obj})

        if serializer.is_valid():
            try:
                serializer.save()
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, assignment, rubric_component, format=None):
        assignment_obj = self.get_assignment(course, assignment)
        rubric_component_obj = self.get_rubric_component(assignment_obj, rubric_component)

        if not (request.user.is_staff or request.user.is_superuser or course.has_instructor(request.user)):
            raise PermissionDenied        
        
        rubric_component_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)        
    
class Register(CourseQualifiedAPIView):
    def get_assignment(self, course, assignment):
        try:
            return Assignment.objects.get(course = course, assignment_id = assignment)
        except Assignment.DoesNotExist:
            raise Http404

    def post(self, request, course, assignment, format=None):
        assignment_obj = self.get_assignment(course, assignment)
    
        user_student_obj = course.get_student(request.user)
        if user_student_obj is None:
            msg = "You are not a student in course '%s'" % (course.course_id)
            return Response({"user": [msg]}, status=status.HTTP_400_BAD_REQUEST)

        # Adding dict() because apparently serializers.ListField won't stomach a QueryDict 
        serializer = RegistrationRequestSerializer(data=dict(request.data))
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)              

        students_usernames = serializer.validated_data["students"]
        if request.user.username not in students_usernames:
            msg = "The list of students does not include you."
            return Response({"students": [msg]}, status=status.HTTP_400_BAD_REQUEST)
            
        students_errors = []
        student_objs = [user_student_obj]
        for student in [s for s in students_usernames if s != request.user.username]:
            user = get_user_by_username(student)
            
            if user is not None:
                student_obj = course.get_student(user)
            else:
                student_obj = None
            
            if user is None or student_obj is None:
                msg = "User '%s' is either not a valid user or not a student in course '%s'" % (student, course.course_id)
                students_errors.append(msg)
            else:
                student_objs.append(student_obj)
                
        if len(students_errors) > 0:
            return Response({"students": students_errors}, status=status.HTTP_400_BAD_REQUEST)
                    
        if len(students_usernames) < assignment_obj.min_students or len(students_usernames) > assignment_obj.max_students:
            if assignment_obj.min_students == assignment_obj.max_students:
                if assignment_obj.min_students == 1:
                    msg = "You specified %i students, but this assignment only accepts individual registrations." % (len(students_usernames))                                    
                else: 
                    msg = "You specified %i students, but this assignment requires teams of %i students" % (len(students_usernames), assignment_obj.min_students)
            else:                
                msg = "You specified %i students, but this assignment requires teams with at least %i students and at most %i students" % (len(students_usernames), assignment_obj.min_students, assignment_obj.max_students)
            return Response({"students": [msg]}, status=status.HTTP_400_BAD_REQUEST)            
            
        create_team = False
        create_registration = False
        teams = course.get_teams_with_students(student_objs)                
                
        if len(teams) > 0:
            # Teams that have the assignment, but are *not* a perfect match
            have_assignment = []
            students_have_assignment = set()
            perfect_match = None
            
            for t in teams:
                team_student_usernames = [u.user.username for u in t.students.all()]
                if len(team_student_usernames) == len(students_usernames):
                    match = True
                    for s in students_usernames:
                        if s not in team_student_usernames:
                            match = False
                            break
                        
                    if match:
                        if perfect_match is None:
                            perfect_match = t
                        else:
                            # There shouldn't be more than one perfect match
                            error_msg = "There is more than one team with the exact same students in it." \
                                        "Please notify your instructor."  
                            return Response({"fatal": [msg]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)            
                    else:
                        if t.is_registered_for_assignment(assignment_obj):
                            have_assignment.append(t)
                            students_have_assignment.update([s for s in team_student_usernames if s in students_usernames])
                else:
                    if t.is_registered_for_assignment(assignment_obj):
                        have_assignment.append(t)
                        students_have_assignment.update([s for s in team_student_usernames if s in students_usernames])

            if len(have_assignment) > 0:
                error_msg = "'%s' is already registered for assignment '%s' in another team"
                error_msgs = [error_msg % (s, assignment_obj.assignment_id) for s in students_have_assignment]
                return Response({"students": error_msgs}, status=status.HTTP_400_BAD_REQUEST)                
                    
            if perfect_match is not None:
                team = perfect_match
                if perfect_match.is_registered_for_assignment(assignment_obj):
                    tm = perfect_match.teammember_set.get(student = user_student_obj)
                    tm.confirmed = True
                    tm.save()
                    
                    registration = perfect_match.get_registration(assignment_obj)
                else:
                    registration = Registration.objects.create(team = perfect_match,
                                                               assignment = assignment_obj)   
                    create_registration = True
            else:
                create_team = True                        
        else:
            create_team = True
            
        if create_team:
            team_name = "-".join(sorted(students_usernames))

            if course.extension_policy == "per-team":
                default_extensions = course.default_extensions
                extensions = default_extensions
            else:
                extensions = 0                
        
            team = Team.objects.create(course = course,
                                       name = team_name,
                                       extensions = extensions)

            for student_obj in student_objs:
                if student_obj.user == request.user:
                    confirmed = True
                else:
                    confirmed = False
                
                team_member = TeamMember.objects.create(student = student_obj,
                                                        team = team,
                                                        confirmed = confirmed)
                
            registration = Registration.objects.create(team = team,
                                                       assignment = assignment_obj)           
            
            create_registration = True     
                
        if create_team or create_registration:
            response_status = status.HTTP_201_CREATED
        else:
            response_status = status.HTTP_200_OK
            
        response_data = {"new_team": create_team,
                         "team": team,
                         "team_members": list(team.get_team_members()),
                         "registration": registration
                         }
            
        serializer = RegistrationResponseSerializer(response_data, context={'request': request, 'course': course})            
        return Response(serializer.data, status=response_status)        
    
class TeamList(CourseQualifiedAPIView):
    def get(self, request, course, format=None):
        student = course.get_student(request.user)
        
        if student is not None:
            teams = course.get_teams_with_students([student])
        else:
            teams = course.get_teams()            
        
        serializer = TeamSerializer(teams, many=True, context={'request': request, 'course': course})
        return Response(serializer.data)

    def post(self, request, course, format=None):
        if not (request.user.is_staff or request.user.is_superuser or course.has_instructor(request.user)):
            raise PermissionDenied

        serializer = TeamSerializer(data=request.data, context={'request': request, 'course': course})
        if serializer.is_valid():
            try:
                serializer.save(course=course)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        
    
    
class TeamDetail(CourseQualifiedAPIView):
            
    def get_team(self, request, course, team):
        try:
            team_obj = Team.objects.get(course = course, name = team)
            student_obj = course.get_student(request.user)
            
            if student_obj is not None:
                if team_obj.get_team_member(student_obj) is None:
                    raise Http404
            return team_obj
        except Team.DoesNotExist:
            raise Http404  

    def get(self, request, course, team, format=None):
        team_obj = self.get_team(request, course, team)
        
        serializer = TeamSerializer(team_obj, context={'request': request, 'course': course})
        return Response(serializer.data)

    def patch(self, request, course, team, format=None):
        team_obj = self.get_team(request, course, team)
        serializer = TeamSerializer(team_obj, data=request.data, partial=True, context={'request': request, 'course': course})        

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, team, format=None):
        team_obj = self.get_team(request, course, team)

        if not (request.user.is_staff or request.user.is_superuser or course.has_instructor(request.user)):
            raise PermissionDenied        
        
        team_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)        
    
class TeamMemberList(CourseQualifiedAPIView):
            
    def get_team(self, course, team):
        try:
            return Team.objects.get(course = course, name = team)
        except Team.DoesNotExist:
            raise Http404              
            
    def get(self, request, course, team, format=None):
        team_obj = self.get_team(course, team)
        
        serializer = TeamMemberSerializer(team_obj.teammember_set.all(), many=True, context={'request': request, 'course': course})
        return Response(serializer.data)

    def post(self, request, course, team, format=None):
        team_obj = self.get_team(course, team)
        
        serializer = TeamMemberSerializer(data=request.data, context={'request': request, 'course': course})
        if serializer.is_valid():
            student = serializer.validated_data["student"]
            if TeamMember.objects.filter(team=team_obj, student=student).exists():
                return Response({"username": ["%s is already a member of team %s" % (student.user.username, team_obj.name)]}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                serializer.save(team = team_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)       
    
class TeamMemberDetail(CourseQualifiedAPIView):
            
    def get_team_member(self, course, team, student):
        try:
            team_obj = Team.objects.get(course = course, name = team)
            teammember_obj = TeamMember.objects.get(team = team_obj, student__user__username = student)
            return teammember_obj
        except (Team.DoesNotExist, TeamMember.DoesNotExist):
            raise Http404  

    def get(self, request, course, team, student, format=None):
        teammember_obj = self.get_team_member(course, team, student)
        serializer = TeamMemberSerializer(teammember_obj, context={'request': request, 'course': course})
        return Response(serializer.data)

    def patch(self, request, course, team, student, format=None):
        teammember_obj = self.get_team_member(course, team, student)
        serializer = TeamMemberSerializer(teammember_obj, data=request.data, partial=True, context={'request': request, 'course': course})        

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, team, student, format=None):
        teammember_obj = self.get_team_member(course, team, student)

        if not (request.user.is_staff or request.user.is_superuser or course.has_instructor(request.user)):
            raise PermissionDenied        
        
        teammember_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)         
    
    
class RegistrationList(CourseQualifiedAPIView):
            
    def get_team(self, course, team):
        try:
            return Team.objects.get(course = course, name = team)
        except Team.DoesNotExist:
            raise Http404              
            
    def get(self, request, course, team, format=None):
        team_obj = self.get_team(course, team)
        
        serializer = RegistrationSerializer(team_obj.registration_set.all(), many=True, context={'request': request, 'course': course})
        return Response(serializer.data)

    def post(self, request, course, team, format=None):
        team_obj = self.get_team(course, team)
        
        serializer = RegistrationSerializer(data=request.data, context={'request': request, 'course': course})
        if serializer.is_valid():
            try:
                serializer.save(team = team_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)       
    
class RegistrationDetail(CourseQualifiedAPIView):
            
    def get_registration(self, course, team, assignment):
        try:
            team_obj = Team.objects.get(course = course, name = team)
            registration_obj = Registration.objects.get(team = team_obj, assignment__assignment_id = assignment)
            return registration_obj
        except (Team.DoesNotExist, Registration.DoesNotExist):
            raise Http404  

    def get(self, request, course, team, assignment, format=None):
        registration_obj = self.get_registration(course, team, assignment)
        serializer = RegistrationSerializer(registration_obj, context={'request': request, 'course': course})
        return Response(serializer.data)

    def patch(self, request, course, team, assignment, format=None):
        registration_obj = self.get_registration(course, team, assignment)
        serializer = RegistrationSerializer(registration_obj, data=request.data, partial=True, context={'request': request, 'course': course})        

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, team, assignment, format=None):
        registration_obj = self.get_registration(course, team, assignment)

        if not (request.user.is_staff or request.user.is_superuser or course.has_instructor(request.user)):
            raise PermissionDenied        
        
        registration_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    
        
class Submit(CourseQualifiedAPIView):
    def get_registration(self, request, course, team, assignment):
        try:
            team_obj = Team.objects.get(course = course, name = team)
            student_obj = course.get_student(request.user)
            
            if student_obj is not None:
                if team_obj.get_team_member(student_obj) is None:
                    raise Http404            
            
            registration_obj = Registration.objects.get(team = team_obj, assignment__assignment_id = assignment)
            return registration_obj
        except (Team.DoesNotExist, Registration.DoesNotExist):
            raise Http404  

    def post(self, request, course, team, assignment, format=None):
        registration_obj = self.get_registration(request, course, team, assignment)
    
        serializer = SubmissionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)              

        now = get_datetime_now_utc()
                
        commit_sha = serializer.validated_data["commit_sha"]
        extensions_requested = serializer.validated_data["extensions"]
        ignore_deadline = serializer.validated_data["ignore_deadline"]
        
        dry_run = request.query_params.get("dry_run", "false") in ("true", "True")
        
        if ignore_deadline:
            if not (request.user.is_staff or request.user.is_superuser or course.has_instructor(request.user)):
                msg = "Nice try! Only admins and instructors can ignore the deadline."
                return Response({"errors": [msg]}, status=status.HTTP_400_BAD_REQUEST)

        if not ignore_deadline and registration_obj.is_ready_for_grading():
            msg = "You cannot re-submit assignment %s." % (registration_obj.assignment.assignment_id)
            msg = " You made a submission before the deadline, and the deadline has passed."
            return Response({"errors": [msg]}, status=status.HTTP_400_BAD_REQUEST)
        
        submission = Submission(registration = registration_obj,
                                extensions_used = extensions_requested,
                                commit_sha = commit_sha,
                                submitted_at = now)
        
        valid, error_response, extensions = submission.validate()
        
        if not valid:
            return error_response
        else:
            if not dry_run:
                submission.save()
                registration_obj.final_submission = submission
                registration_obj.save()
                response_status = status.HTTP_201_CREATED
            else:
                response_status = status.HTTP_200_OK
            
            response_data = {"submission": submission,
                             "extensions_before": extensions["extensions_available_before"],
                             "extensions_after": extensions["extensions_available_after"]
                             }
                
            serializer = SubmissionResponseSerializer(response_data, context={'request': request, 'course': course})            
            return Response(serializer.data, status=response_status)        
        

class SubmissionList(CourseQualifiedAPIView):
            
    def get_registration(self, request, course, team, assignment):
        try:
            team_obj = Team.objects.get(course = course, name = team)
            student_obj = course.get_student(request.user)
            
            if student_obj is not None:
                if team_obj.get_team_member(student_obj) is None:
                    raise Http404            
            
            registration_obj = Registration.objects.get(team = team_obj, assignment__assignment_id = assignment)
            return registration_obj
        except (Team.DoesNotExist, Registration.DoesNotExist):
            raise Http404          
            
    def get(self, request, course, team, assignment, format=None):
        registration_obj = self.get_registration(request, course, team, assignment)
        
        serializer = SubmissionSerializer(registration_obj.submission_set.all(), many=True, context={'request': request, 'course': course})
        return Response(serializer.data)

    def post(self, request, course, team, assignment, format=None):
        registration_obj = self.get_registration(request, course, team, assignment)
        
        serializer = SubmissionSerializer(data=request.data, context={'request': request, 'course': course})
        if serializer.is_valid():
            try:
                serializer.save(registration = registration_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)       
    
class SubmissionDetail(CourseQualifiedAPIView):
    
    def get_submission(self, request, course, team, assignment, submission):
        try:
            team_obj = Team.objects.get(course = course, name = team)
            student_obj = course.get_student(request.user)
            
            if student_obj is not None:
                if team_obj.get_team_member(student_obj) is None:
                    raise Http404            
            
            registration_obj = Registration.objects.get(team = team_obj, assignment__assignment_id = assignment)
            submission_obj = Submission.objects.get(registration = registration_obj, pk = submission)
            
            return submission_obj
        except (Team.DoesNotExist, Registration.DoesNotExist, Submission.DoesNotExist):
            raise Http404       
    
    def get(self, request, course, team, assignment, submission, format=None):
        submission_obj = self.get_submission(request, course, team, assignment, submission)
        serializer = SubmissionSerializer(submission_obj, context={'request': request, 'course': course})
        return Response(serializer.data)

    def patch(self, request, course, team, assignment, submission, format=None):
        submission_obj = self.get_submission(request, course, team, assignment, submission)
        serializer = SubmissionSerializer(submission_obj, data=request.data, partial=True, context={'request': request, 'course': course})        

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, team, assignment, submission, format=None):
        submission_obj = self.get_submission(course, team, assignment)

        if not (request.user.is_staff or request.user.is_superuser or course.has_instructor(request.user)):
            raise PermissionDenied        
        
        submission_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    

class GradeList(CourseQualifiedAPIView):
            
    def get_registration(self, request, course, team, assignment):
        try:
            team_obj = Team.objects.get(course = course, name = team)
            student_obj = course.get_student(request.user)
            
            if student_obj is not None:
                if team_obj.get_team_member(student_obj) is None:
                    raise Http404            
            
            registration_obj = Registration.objects.get(team = team_obj, assignment__assignment_id = assignment)
            return registration_obj
        except (Team.DoesNotExist, Registration.DoesNotExist):
            raise Http404          
            
    def get(self, request, course, team, assignment, format=None):
        registration_obj = self.get_registration(request, course, team, assignment)
        
        serializer = GradeSerializer(registration_obj.grade_set.all(), many=True, context={'request': request, 'course': course})
        return Response(serializer.data)

    def post(self, request, course, team, assignment, format=None):
        registration_obj = self.get_registration(request, course, team, assignment)
        
        serializer = GradeSerializer(data=request.data, context={'request': request, 'course': course})
        if serializer.is_valid():
            try:
                serializer.save(registration = registration_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)       
    
class GradeDetail(CourseQualifiedAPIView):
    
    def get_grade(self, request, course, team, assignment, grade):
        try:
            team_obj = Team.objects.get(course = course, name = team)
            student_obj = course.get_student(request.user)
            
            if student_obj is not None:
                if team_obj.get_team_member(student_obj) is None:
                    raise Http404            
            
            registration_obj = Registration.objects.get(team = team_obj, assignment__assignment_id = assignment)
            grade_obj = Grade.objects.get(registration = registration_obj, pk = grade)
            
            return grade_obj
        except (Team.DoesNotExist, Registration.DoesNotExist, Grade.DoesNotExist):
            raise Http404       
    
    def get(self, request, course, team, assignment, grade, format=None):
        grade_obj = self.get_submission(request, course, team, assignment, grade)
        serializer = SubmissionSerializer(grade_obj, context={'request': request, 'course': course})
        return Response(serializer.data)

    def patch(self, request, course, team, assignment, grade, format=None):
        grade_obj = self.get_submission(request, course, team, assignment, grade)
        serializer = SubmissionSerializer(grade_obj, data=request.data, partial=True, context={'request': request, 'course': course})        

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course, team, assignment, grade, format=None):
        grade_obj = self.get_submission(course, team, assignment)

        if not (request.user.is_staff or request.user.is_superuser or course.has_instructor(request.user)):
            raise PermissionDenied        
        
        grade_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    

    
class UserList(APIView):
    def get(self, request, format=None):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied
        users = User.objects.all()
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, format=None):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied
        serializer = UserSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            try:
                user = User.objects.get(username=username)
                msg = "There is already a username with username = %s" % (username)
                return Response({"username": [msg]}, status=status.HTTP_400_BAD_REQUEST)                               
            except User.DoesNotExist:
                try:
                    serializer.save()
                except Error, e:
                    return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    
class BaseUserDetail(APIView):
            
    def get_user(self, username):
        try:
            user = User.objects.get(username = username)
            return user
        except User.DoesNotExist:
            raise Http404  
            
    def _get(self, request, username, format=None):
        if username != request.user.username and not (request.user.is_staff or request.user.is_superuser):
            raise Http404        
        user = self.get_user(username)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    def _patch(self, request, username, format=None):
        if not (request.user.is_staff or request.user.is_superuser):
            if username == request.user.username:
                raise PermissionDenied
            else:
                raise Http404  
                  
        user = self.get_user(username)
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})        
        if serializer.is_valid():
            try:
                serializer.save()
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _delete(self, request, username, format=None):
        if not (request.user.is_staff or request.user.is_superuser):
            if username == request.user.username:
                raise PermissionDenied
            else:
                raise Http404  
        user = self.get_user(username)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    
    
class UserDetail(BaseUserDetail):    
    
    def get(self, request, username, format=None):
        return self._get(request, username, format)

    def patch(self, request, username, format=None):
        return self._patch(request, username, format)

    def delete(self, request, username, format=None):
        return self._delete(request, username, format)    
    
class AuthUserDetail(BaseUserDetail):    
    
    def get(self, request, format=None):
        return self._get(request, request.user.username, format)

    def patch(self, request, format=None):
        return self._patch(request, request.user.username, format)

    def delete(self, request, format=None):
        return self._delete(request, request.user.username, format)
    
class BaseUserToken(APIView):
    
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    
    def _get(self, request, username, format=None):
        try:
            user = User.objects.get(username = username)
        except User.DoesNotExist:
            raise Http404          
        
        if not (request.user.is_staff or request.user.is_superuser or username == request.user.username):
            raise Http404
        
        reset = "true" in request.query_params.get("reset", [])
        
        if reset:
            try:
                token = Token.objects.get(user__username=username)
                old_token = token.key
                token.delete()
            except Token.DoesNotExist:
                old_token = None
        
            token = Token.objects.create(user=user)
            
            return Response({'old_token': old_token, 'token': token.key, 'new': True}, status=status.HTTP_201_CREATED)
        else:
            token, created = Token.objects.get_or_create(user=user)
        
            if created:
                return Response({'old_token': None, 'token': token.key, 'new': True}, status=status.HTTP_201_CREATED)
            else:
                return Response({'old_token': None, 'token': token.key, 'new': False}, status=status.HTTP_200_OK)
            
class UserToken(BaseUserToken):    
    
    def get(self, request, username, format=None):
        return self._get(request, username, format)

    
class AuthUserToken(BaseUserToken):    
    
    def get(self, request, format=None):
        return self._get(request, request.user.username, format)
        



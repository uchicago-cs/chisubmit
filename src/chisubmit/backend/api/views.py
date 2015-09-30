from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chisubmit.backend.api.models import Course, Student, Instructor, Grader,\
    Assignment, Team, RubricComponent, get_user_by_username, TeamMember,\
    Registration, Submission, Grade, CourseRoles
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
from chisubmit.common.utils import get_datetime_now_utc
from chisubmit.backend.api.helpers import get_course_person, get_assignment,\
    get_team, get_course, get_rubric_component, get_team_member,\
    get_registration, get_submission, get_grade

class CourseList(APIView):
    def get(self, request, format=None):
        courses = Course.objects.all()
        if not (request.user.is_staff or request.user.is_superuser):
            courses = [c for c in courses if c.has_user(request.user)]
        response_courses = []
        for course in courses:
            serializer = CourseSerializer(course, context={'request': request, 'course': course})
            response_courses.append(serializer.data)
        return Response(response_courses)

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

  
class CourseDetail(APIView):
            
    def get(self, request, course_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        serializer = CourseSerializer(course_obj, context=serializer_context)
        
        return Response(serializer.data)

    def patch(self, request, course_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        serializer = CourseSerializer(course_obj, data=request.data, partial=True, context=serializer_context)
        
        if serializer.is_valid():
            try:
                serializer.save()
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, format=None):
        course_obj, roles = get_course(request, course_id)
        
        if not CourseRoles.ADMIN in roles:
            raise PermissionDenied
        
        course_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
                
 
class PersonList(APIView):
    def get(self, request, course_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles or CourseRoles.GRADER in roles):
            raise PermissionDenied
        
        persons = self.person_class.objects.filter(course = course_obj)
        
        serializer = self.person_serializer(persons, many=True, context=serializer_context)
        return Response(serializer.data)

    def post(self, request, course_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        if not CourseRoles.ADMIN in roles:
            raise PermissionDenied
        
        serializer = self.person_serializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            if self.person_class.objects.filter(course=course_obj, user=request.user).exists():
                return Response({"username": ["%s is already a %s in %s" % (user.username, self.person_str, course_obj.course_id)]}, status=status.HTTP_400_BAD_REQUEST)

            try:
                serializer.save(course=course_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PersonDetail(APIView):
            
    def get_person(self, request, course_obj, roles, username):
        return get_course_person(course_obj, request.user, roles, self.person_class, username)
            
    def get(self, request, course_id, username, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}        
        
        person_obj = self.get_person(request, course_obj, roles, username)
        serializer_context["is_owner"] = (request.user.username == username)
        serializer = self.person_serializer(person_obj, context=serializer_context)
        return Response(serializer.data)

    def patch(self, request, course_id, username, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}        
        
        person_obj = self.get_person(request, course_obj, roles, username)
        serializer_context["is_owner"] = (request.user.username == username)

        serializer = self.person_serializer(person_obj, data=request.data, partial=True, context=serializer_context)        

        if serializer.is_valid():
            try:
                serializer.save()
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, username, format=None):
        course_obj, roles = get_course(request, course_id)
        person_obj = self.get_person(request, course_obj, roles, username)
        
        if not (CourseRoles.ADMIN in roles):
            raise PermissionDenied
        
        person_obj.delete()
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
    
    
class AssignmentList(APIView):
    def get(self, request, course_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}   
                
        assignments = Assignment.objects.filter(course = course_obj)
        serializer = AssignmentSerializer(assignments, many=True, context=serializer_context)
        return Response(serializer.data)

    def post(self, request, course_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}   

        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied

        serializer = AssignmentSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            assignment_id = serializer.validated_data["assignment_id"]
            if course_obj.get_assignment(assignment_id) is not None:
                msg = "There is already an assignment in course %s with assignment_id = %s" % (course_obj.course_id, assignment_id)
                return Response({"assignment_id": [msg]}, status=status.HTTP_400_BAD_REQUEST)   
            try:
                serializer.save(course=course_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    

class AssignmentDetail(APIView):

    def get(self, request, course_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}   
        
        assignment_obj = get_assignment(course_obj, request.user, roles, assignment_id)
        serializer = AssignmentSerializer(assignment_obj, context=serializer_context)
        
        return Response(serializer.data)

    def patch(self, request, course_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}   
        
        assignment_obj = get_assignment(course_obj, request.user, roles, assignment_id)
        serializer = AssignmentSerializer(assignment_obj, data=request.data, partial=True, context=serializer_context)        

        if serializer.is_valid():
            try:
                serializer.save()
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        
        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied        

        assignment_obj = get_assignment(course_obj, request.user, roles, assignment_id)
        assignment_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    
    

class RubricList(APIView):
   
    def get(self, request, course_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
                   
        assignment_obj = get_assignment(course_obj, request.user, roles, assignment_id)        
        rubric_components = assignment_obj.get_rubric_components()
        
        serializer = RubricComponentSerializer(rubric_components, many=True, context=serializer_context)
        return Response(serializer.data)

    def post(self, request, course_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
                   
        assignment_obj = get_assignment(course_obj, request.user, roles, assignment_id)        
        serializer = RubricComponentSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            description = serializer.validated_data["description"]
            rubric_description = assignment_obj.get_rubric_component_by_description(description)
            if rubric_description is not None:
                msg = "There is already a rubric component in assignment %s with description = '%s'" % (assignment_id, description)
                return Response({"description": [msg]}, status=status.HTTP_400_BAD_REQUEST)   
            try:
                serializer.save(assignment = assignment_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    

class RubricDetail(APIView):

    def get(self, request, course_id, assignment_id, rubric_component_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
                   
        rubric_component_obj = get_rubric_component(course_obj, request.user, roles, assignment_id)   
        serializer = RubricComponentSerializer(rubric_component_obj, context=serializer_context)
        return Response(serializer.data)

    def patch(self, request, course_id, assignment_id, rubric_component_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
                   
        rubric_component_obj = get_rubric_component(course_obj, request.user, roles, assignment_id, rubric_component_id)   
        serializer = RubricComponentSerializer(rubric_component_obj, data=request.data, partial=True, context=serializer_context)

        if serializer.is_valid():
            try:
                serializer.save()
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, assignment_id, rubric_component_id, format=None):
        course_obj, roles = get_course(request, course_id)
        rubric_component_obj = get_rubric_component(course_obj, request.user, roles, assignment_id, rubric_component_id)   

        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied
                
        rubric_component_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)        


class Register(APIView):

    def post(self, request, course_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}

        assignment_obj = get_assignment(course_obj, request.user, roles, assignment_id)        
    
        # Adding dict() because apparently serializers.ListField won't stomach a QueryDict 
        serializer = RegistrationRequestSerializer(data=dict(request.data))
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)              

        students_usernames = serializer.validated_data["students"]

        if len(roles) == 1 and CourseRoles.STUDENT in roles:
            is_student = True
            
            if request.user.username not in students_usernames:
                msg = "The list of students does not include you."
                return Response({"students": [msg]}, status=status.HTTP_400_BAD_REQUEST)
            
            user_student_obj = course_obj.get_student(request.user)
            student_objs = [user_student_obj]
            other_students = [s for s in students_usernames if s != request.user.username]
        else:
            is_student = False
            
            student_objs = []
            other_students = students_usernames

        students_errors = []
        for student in other_students:
            user_obj = get_user_by_username(student)
            
            if user_obj is not None:
                student_obj = course_obj.get_student(user_obj)
            else:
                student_obj = None
            
            if user_obj is None or student_obj is None:
                msg = "User '%s' is either not a valid user or not a student in course '%s'" % (student, course_obj.course_id)
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
        teams = course_obj.get_teams_with_students(student_objs)                
                
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
            team_id = "-".join(sorted(students_usernames))

            if course_obj.extension_policy == Course.EXT_PER_TEAM:
                default_extensions = course_obj.default_extensions
                extensions = default_extensions
            else:
                extensions = 0              
        
            team = Team.objects.create(course = course_obj,
                                       team_id = team_id,
                                       extensions = extensions)

            for student_obj in student_objs:
                if student_obj.user == request.user or not is_student:
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
            
        serializer = RegistrationResponseSerializer(response_data, context=serializer_context)            
        return Response(serializer.data, status=response_status)        
    

class TeamList(APIView):
    def get(self, request, course_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        if (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles or CourseRoles.GRADER in roles):
            teams = course_obj.get_teams()            
        elif len(roles) == 1 and CourseRoles.STUDENT in roles:
            student = course_obj.get_student(request.user)  
            teams = course_obj.get_teams_with_students([student])
        else:
            teams = []
        
        serializer = TeamSerializer(teams, many=True, context=serializer_context)
        return Response(serializer.data)

    def post(self, request, course_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied

        serializer = TeamSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            try:
                serializer.save(course=course_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        
    
    
class TeamDetail(APIView):
            
    def get(self, request, course_id, team_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        team_obj = get_team(course_obj, request.user, roles, team_id)
        
        serializer = TeamSerializer(team_obj, context=serializer_context)
        return Response(serializer.data)

    def patch(self, request, course_id, team_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        team_obj = get_team(course_obj, request.user, roles, team_id)
        serializer = TeamSerializer(team_obj, data=request.data, partial=True, context=serializer_context)        

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, team_id, format=None):
        course_obj, roles = get_course(request, course_id)
        team_obj = get_team(course_obj, request.user, roles, team_id)

        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied        
        
        team_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)        
    

class TeamMemberList(APIView):            
            
    def get(self, request, course_id, team_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        team_obj = get_team(course_obj, request.user, roles, team_id)
        
        serializer = TeamMemberSerializer(team_obj.teammember_set.all(), many=True, context=serializer_context)
        return Response(serializer.data)

    def post(self, request, course_id, team_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied        
        
        team_obj = get_team(course_obj, request.user, roles, team_id)

        serializer = TeamMemberSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            student = serializer.validated_data["student"]
            if TeamMember.objects.filter(team=team_obj, student=student).exists():
                return Response({"username": ["%s is already a member of team %s" % (student.user.username, team_obj.team_id)]}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                serializer.save(team = team_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)       


class TeamMemberDetail(APIView):
            
    def get(self, request, course_id, team_id, student_username, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
                
        teammember_obj = get_team_member(course_obj, request.user, roles, team_id, student_username)
        serializer = TeamMemberSerializer(teammember_obj, context=serializer_context)
        return Response(serializer.data)

    def patch(self, request, course_id, team_id, student_username, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
                
        teammember_obj = get_team_member(course_obj, request.user, roles, team_id, student_username)
        serializer = TeamMemberSerializer(teammember_obj, data=request.data, partial=True, context=serializer_context)        

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, team_id, student_username, format=None):
        course_obj, roles = get_course(request, course_id)              
        teammember_obj = get_team_member(course_obj, request.user, roles, team_id, student_username)

        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied
        
        teammember_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)         
    
    
class RegistrationList(APIView):        
            
    def get(self, request, course_id, team_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        team_obj = get_team(course_obj, request.user, roles, team_id)
        
        serializer = RegistrationSerializer(team_obj.registration_set.all(), many=True, context=serializer_context)
        return Response(serializer.data)

    def post(self, request, course_id, team_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        team_obj = get_team(course_obj, request.user, roles, team_id)
        
        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied        
        
        serializer = RegistrationSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            try:
                serializer.save(team = team_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)       
    

class RegistrationDetail(APIView):

    def get(self, request, course_id, team_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        registration_obj = get_registration(course_obj, request.user, roles, team_id, assignment_id)
        
        serializer = RegistrationSerializer(registration_obj, context=serializer_context)
        return Response(serializer.data)

    def patch(self, request, course_id, team_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        registration_obj = get_registration(course_obj, request.user, roles, team_id, assignment_id)
        serializer = RegistrationSerializer(registration_obj, data=request.data, partial=True, context=serializer_context)        

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, team_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        registration_obj = get_registration(course_obj, request.user, roles, team_id, assignment_id)

        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied
        
        registration_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    
    

class Submit(APIView):

    def post(self, request, course_id, team_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        registration_obj = get_registration(course_obj, request.user, roles, team_id, assignment_id)
    
        serializer = SubmissionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)              

        now = get_datetime_now_utc()
                
        commit_sha = serializer.validated_data["commit_sha"]
        extensions_requested = serializer.validated_data["extensions"]
        ignore_deadline = serializer.validated_data["ignore_deadline"]
        
        dry_run = request.query_params.get("dry_run", "false") in ("true", "True")
        
        if ignore_deadline:
            if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
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
                
            serializer = SubmissionResponseSerializer(response_data, context=serializer_context)            
            return Response(serializer.data, status=response_status)        
        

class SubmissionList(APIView):     
            
    def get(self, request, course_id, team_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        registration_obj = get_registration(course_obj, request.user, roles, team_id, assignment_id)
        
        serializer = SubmissionSerializer(registration_obj.submission_set.all(), many=True, context=serializer_context)
        return Response(serializer.data)

    def post(self, request, course_id, team_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        registration_obj = get_registration(course_obj, request.user, roles, team_id, assignment_id)

        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied
        
        serializer = SubmissionSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            try:
                serializer.save(registration = registration_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)       
    
class SubmissionDetail(APIView):
    
    def get(self, request, course_id, team_id, assignment_id, submission_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}

        submission_obj = get_submission(course_obj, request.user, roles, team_id, assignment_id, submission_id)
        serializer = SubmissionSerializer(submission_obj, context=serializer_context)
        return Response(serializer.data)

    def patch(self, request, course_id, team_id, assignment_id, submission_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}

        submission_obj = get_submission(course_obj, request.user, roles, team_id, assignment_id, submission_id)
        serializer = SubmissionSerializer(submission_obj, data=request.data, partial=True, context=serializer_context)        

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, team_id, assignment_id, submission_id, format=None):
        course_obj, roles = get_course(request, course_id)
        submission_obj = get_submission(course_obj, request.user, roles, team_id, assignment_id, submission_id)

        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied
        
        submission_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    

class GradeList(APIView):
            
    def get(self, request, course_id, team_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        registration_obj = get_registration(course_obj, request.user, roles, team_id, assignment_id)
        
        serializer = GradeSerializer(registration_obj.grade_set.all(), many=True, context=serializer_context)
        return Response(serializer.data)

    def post(self, request, course_id, team_id, assignment_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}
        
        registration_obj = get_registration(course_obj, request.user, roles, team_id, assignment_id)
        
        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
            raise PermissionDenied
        
        serializer = GradeSerializer(data=request.data, context=serializer_context)
        if serializer.is_valid():
            try:
                serializer.save(registration = registration_obj)
            except Error, e:
                return Response({"database": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)       
    
class GradeDetail(APIView): 
    
    def get(self, request, course_id, team_id, assignment_id, grade_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}

        grade_obj = get_grade(course_obj, request.user, roles, team_id, assignment_id, grade_id)
        serializer = GradeSerializer(grade_obj, context=serializer_context)
        return Response(serializer.data)

    def patch(self, request, course_id, team_id, assignment_id, grade_id, format=None):
        course_obj, roles = get_course(request, course_id)
        serializer_context = {'request': request, 'course': course_obj, 'roles': roles}

        grade_obj = get_grade(course_obj, request.user, roles, team_id, assignment_id, grade_id)
        serializer = GradeSerializer(grade_obj, data=request.data, partial=True, context=serializer_context)        
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, team_id, assignment_id, grade_id, format=None):
        course_obj, roles = get_course(request, course_id)
        grade_obj = get_grade(course_obj, request.user, roles, team_id, assignment_id, grade_id)

        if not (CourseRoles.ADMIN in roles or CourseRoles.INSTRUCTOR in roles):
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
        



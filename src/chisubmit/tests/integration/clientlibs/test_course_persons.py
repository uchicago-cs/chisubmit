from chisubmit.backend.api.models import Course, TeamMember
from chisubmit.tests.integration.clientlibs import ChisubmitClientLibsTestCase
from chisubmit.tests.common import COURSE1_GRADERS, COURSE1_STUDENTS, COURSE1_INSTRUCTORS

class CoursePersonTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_users']
    
    def test_get_instructors(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        instructors = course.get_instructors()
        
        self.assertEquals(len(instructors), len(COURSE1_INSTRUCTORS))
        self.assertItemsEqual([i.username for i in instructors], COURSE1_INSTRUCTORS)
        
    def test_add_instructor_by_username(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40100")
        self.assertFalse(course_obj.instructors.filter(username="instructor2").exists())
        
        course = c.get_course("cmsc40100")
        instructor = course.add_instructor("instructor2")
        
        self.assertEquals(instructor.username, "instructor2")
        self.assertEquals(instructor.user.first_name, "F_instructor2")
        self.assertEquals(instructor.user.last_name, "L_instructor2")

        self.assertTrue(course_obj.instructors.filter(username="instructor2").exists())      
        
    def test_add_instructor_by_user(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40100")
        self.assertFalse(course_obj.instructors.filter(username="instructor2").exists())
        
        course = c.get_course("cmsc40100")
        user = c.get_user("instructor2")
        instructor = course.add_instructor(user)
        
        self.assertEquals(instructor.username, "instructor2")
        self.assertEquals(instructor.user.first_name, "F_instructor2")
        self.assertEquals(instructor.user.last_name, "L_instructor2")

        self.assertTrue(course_obj.instructors.filter(username="instructor2").exists())        
        
    def test_remove_instructor(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40100")
        self.assertTrue(course_obj.instructors.filter(username="instructor1").exists())
        
        course = c.get_course("cmsc40100")
        course.remove_instructor("instructor1")
        
        self.assertFalse(course_obj.instructors.filter(username="instructor1").exists())
        
    def test_get_graders(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        graders = course.get_graders()
        
        self.assertEquals(len(graders), len(COURSE1_GRADERS))
        self.assertItemsEqual([g.username for g in graders], COURSE1_GRADERS)
                
    def test_add_grader_by_username(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40100")
        self.assertFalse(course_obj.graders.filter(username="grader3").exists())
        
        course = c.get_course("cmsc40100")
        grader = course.add_grader("grader3")
        
        self.assertEquals(grader.username, "grader3")
        self.assertEquals(grader.user.first_name, "F_grader3")
        self.assertEquals(grader.user.last_name, "L_grader3")

        self.assertTrue(course_obj.graders.filter(username="grader3").exists())      
        
    def test_add_grader_by_user(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40100")
        self.assertFalse(course_obj.graders.filter(username="grader3").exists())
        
        course = c.get_course("cmsc40100")
        user = c.get_user("grader3")
        grader = course.add_grader(user)
        
        self.assertEquals(grader.username, "grader3")
        self.assertEquals(grader.user.first_name, "F_grader3")
        self.assertEquals(grader.user.last_name, "L_grader3")

        self.assertTrue(course_obj.graders.filter(username="grader3").exists())                   
                
    def test_remove_grader(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40100")
        self.assertTrue(course_obj.graders.filter(username="grader1").exists())
        
        course = c.get_course("cmsc40100")
        course.remove_grader("grader1")
        
        self.assertFalse(course_obj.graders.filter(username="grader1").exists())                
                
    def test_get_students(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        students = course.get_students()
        
        self.assertEquals(len(students), len(COURSE1_STUDENTS))
        self.assertItemsEqual([s.username for s in students], COURSE1_STUDENTS)      
        
    def test_add_student_by_username(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40100")
        self.assertFalse(course_obj.students.filter(username="student5").exists())
        
        course = c.get_course("cmsc40100")
        student = course.add_student("student5")
        
        self.assertEquals(student.username, "student5")
        self.assertEquals(student.user.first_name, "F_student5")
        self.assertEquals(student.user.last_name, "L_student5")

        self.assertTrue(course_obj.students.filter(username="student5").exists())      
        
    def test_add_student_by_user(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40100")
        self.assertFalse(course_obj.students.filter(username="student5").exists())
        
        course = c.get_course("cmsc40100")
        user = c.get_user("student5")
        student = course.add_student(user)
        
        self.assertEquals(student.username, "student5")
        self.assertEquals(student.user.first_name, "F_student5")
        self.assertEquals(student.user.last_name, "L_student5")

        self.assertTrue(course_obj.students.filter(username="student5").exists())    
        
    def test_remove_student(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40100")
        self.assertTrue(course_obj.students.filter(username="student1").exists())
        
        course = c.get_course("cmsc40100")
        course.remove_student("student1")
        
        self.assertFalse(course_obj.students.filter(username="student1").exists())   
        
class MultiCoursePersonTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 'course2']        
                
    def test_add_instructor(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40110")
        self.assertFalse(course_obj.instructors.filter(username="instructor1").exists())
        
        course = c.get_course("cmsc40110")
        instructor = course.add_instructor("instructor1")
        
        self.assertEquals(instructor.username, "instructor1")
        self.assertEquals(instructor.user.first_name, "F_instructor1")
        self.assertEquals(instructor.user.last_name, "L_instructor1")

        self.assertTrue(course_obj.instructors.filter(username="instructor1").exists())       
        
    def test_add_grader(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40110")
        self.assertFalse(course_obj.graders.filter(username="grader1").exists())
        
        course = c.get_course("cmsc40110")
        grader = course.add_grader("grader1")
        
        self.assertEquals(grader.username, "grader1")
        self.assertEquals(grader.user.first_name, "F_grader1")
        self.assertEquals(grader.user.last_name, "L_grader1")

        self.assertTrue(course_obj.graders.filter(username="grader1").exists())             
        
    def test_add_student(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40110")
        self.assertFalse(course_obj.students.filter(username="student1").exists())
        
        course = c.get_course("cmsc40110")
        student = course.add_student("student1")
        
        self.assertEquals(student.username, "student1")
        self.assertEquals(student.user.first_name, "F_student1")
        self.assertEquals(student.user.last_name, "L_student1")

        self.assertTrue(course_obj.students.filter(username="student1").exists())
        
    def test_add_team(self):
        c = self.get_api_client("admintoken")

        course_obj = Course.objects.get(course_id="cmsc40110")
        self.assertFalse(course_obj.students.filter(username="student1").exists())
        
        course = c.get_course("cmsc40110")
        course.add_student("student1")
        course.add_student("student2")
        
        team = course.create_team(team_id = "student1-student2",
                                  extensions = 2,
                                  active = True)
        self.assertEquals(team.team_id, "student1-student2")
        self.assertEquals(team.extensions, 2)
        self.assertEquals(team.active, True)
               
        team_obj = course_obj.get_team("student1-student2")
        self.assertIsNotNone(team_obj, "Team was not added to database")
            
        self.assertEquals(team_obj.team_id, "student1-student2")                  
        self.assertEquals(team_obj.extensions, 2)                  
        self.assertEquals(team_obj.active, True)
              
        team_member = team.add_team_member("student1", confirmed = True)
        self.assertEqual(team_member.username, "student1")
        self.assertEqual(team_member.student.user.username, "student1")
        self.assertEqual(team_member.confirmed, True)
                
        team_member_objs = TeamMember.objects.filter(team = team_obj, student__user__username = "student1")
        self.assertEquals(len(team_member_objs), 1)
        team_member_obj = team_member_objs[0]
        self.assertEqual(team_member_obj.student.user.username, "student1")
        self.assertEqual(team_member_obj.confirmed, True)

        team_member = team.add_team_member("student2", confirmed = True)
        self.assertEqual(team_member.username, "student2")
        self.assertEqual(team_member.student.user.username, "student2")
        self.assertEqual(team_member.confirmed, True)
                
        team_member_objs = TeamMember.objects.filter(team = team_obj, student__user__username = "student2")
        self.assertEquals(len(team_member_objs), 1)
        team_member_obj = team_member_objs[0]
        self.assertEqual(team_member_obj.student.user.username, "student2")
        self.assertEqual(team_member_obj.confirmed, True)
        
        team_members = team.get_team_members()
        
        self.assertEquals(len(team_members), 2)
        self.assertItemsEqual([tm.username for tm in team_members], ["student1","student2"])
        self.assertItemsEqual([tm.student.user.username for tm in team_members], ["student1","student2"])             
        
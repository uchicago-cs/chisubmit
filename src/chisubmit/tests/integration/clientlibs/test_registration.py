from chisubmit.tests.integration.clientlibs import ChisubmitClientLibsTestCase
from chisubmit.client.exceptions import BadRequestException

class RegistrationTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                         'course1_pa1', 'course1_pa1_registrations',
                         'course1_pa2']
    
    def test_register_existing_team(self):
        c = self.get_api_client("student1token")
        
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")

        students = ["student1", "student2"]

        r = assignment.register(students = students)
                                
        self.assertEquals(r.new_team, False)          
        self.assertEquals(r.team.team_id, "student1-student2")
        self.assertItemsEqual([tm.username for tm in r.team_members], students)
        self.assertEquals(r.registration.assignment_id, "pa2")
        self.assertEquals(r.registration.assignment.assignment_id, "pa2")
        
    def test_register_new_team_single_student(self):
        c = self.get_api_client("student1token")
        
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")

        students = ["student1", "student3"]

        r = assignment.register(students = students)
                                
        self.assertEquals(r.new_team, True)          
        self.assertEquals(r.team.team_id, "student1-student3")
        self.assertItemsEqual([tm.username for tm in r.team_members], students)
        self.assertEquals(r.registration.assignment_id, "pa2")
        self.assertEquals(r.registration.assignment.assignment_id, "pa2")
        
    def test_register_new_team(self):
        students = ["student1", "student3"]

        c = self.get_api_client("student1token")
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")
        r = assignment.register(students = students)
                                
        self.assertEquals(r.new_team, True)          
        self.assertEquals(r.team.team_id, "student1-student3")
        self.assertItemsEqual([tm.username for tm in r.team_members], students)
        self.assertEquals(r.registration.assignment_id, "pa2")
        self.assertEquals(r.registration.assignment.assignment_id, "pa2")          

        c = self.get_api_client("student3token")
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")
        r = assignment.register(students = students)
                                
        self.assertEquals(r.new_team, False)          
        self.assertEquals(r.team.team_id, "student1-student3")
        self.assertItemsEqual([tm.username for tm in r.team_members], students)
        self.assertItemsEqual([tm.confirmed for tm in r.team_members], [True, True])
        self.assertEquals(r.registration.assignment_id, "pa2")
        self.assertEquals(r.registration.assignment.assignment_id, "pa2")
        
    def test_register_new_team_redundant(self):
        students = ["student1", "student3"]

        c = self.get_api_client("student1token")
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")
        r = assignment.register(students = students)
                                
        self.assertEquals(r.new_team, True)          
        self.assertEquals(r.team.team_id, "student1-student3")
        self.assertItemsEqual([tm.username for tm in r.team_members], students)
        self.assertEquals(r.registration.assignment_id, "pa2")
        self.assertEquals(r.registration.assignment.assignment_id, "pa2")          

        c = self.get_api_client("student3token")
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")
        r = assignment.register(students = students)
                                
        self.assertEquals(r.new_team, False)          
        self.assertEquals(r.team.team_id, "student1-student3")
        self.assertItemsEqual([tm.username for tm in r.team_members], students)
        self.assertItemsEqual([tm.confirmed for tm in r.team_members], [True, True])
        self.assertEquals(r.registration.assignment_id, "pa2")
        self.assertEquals(r.registration.assignment.assignment_id, "pa2")         
        
        c = self.get_api_client("student1token")
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")
        r = assignment.register(students = students)
                                
        self.assertEquals(r.new_team, False)          
        self.assertEquals(r.team.team_id, "student1-student3")
        self.assertItemsEqual([tm.username for tm in r.team_members], students)
        self.assertItemsEqual([tm.confirmed for tm in r.team_members], [True, True])
        self.assertEquals(r.registration.assignment_id, "pa2")
        self.assertEquals(r.registration.assignment.assignment_id, "pa2")                
        
    def test_register_non_student(self):
        c = self.get_api_client("instructor1token")
        
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")

        students = ["student1", "student2"]

        r = assignment.register(students = students)
                                
        self.assertEquals(r.new_team, False)          
        self.assertEquals(r.team.team_id, "student1-student2")
        self.assertItemsEqual([tm.username for tm in r.team_members], students)
        self.assertEquals(r.registration.assignment_id, "pa2")
        self.assertEquals(r.registration.assignment.assignment_id, "pa2") 
        
        
class RegistrationErrorTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                         'course1_pa1', 'course1_pa1_registrations',
                         'course1_pa2']
                
    def test_register_other_student(self):
        c = self.get_api_client("student1token")
        
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")

        students = ["student2", "student3"]

        with self.assertRaises(BadRequestException) as cm:
            r = assignment.register(students = students)
        
    def test_register_student_in_other_class(self):
        c = self.get_api_client("student1token")
        
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")

        students = ["student1", "student5"]

        with self.assertRaises(BadRequestException) as cm:
            r = assignment.register(students = students)
        
    def test_register_wrong_number_of_students(self):
        c = self.get_api_client("student1token")
        
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa2")

        students = ["student1", "student2", "student3"]

        with self.assertRaises(BadRequestException) as cm:
            r = assignment.register(students = students)        
            
    def test_register_multiple_groups(self):
        c = self.get_api_client("student1token")
        
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa1")

        students = ["student1", "student3"]

        with self.assertRaises(BadRequestException) as cm:
            r = assignment.register(students = students)               
        
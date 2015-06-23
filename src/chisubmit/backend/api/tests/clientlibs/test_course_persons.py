from chisubmit.backend.api.models import Course
from chisubmit.backend.api.tests.clientlibs import ChisubmitClientLibsTests,\
    COURSE1_USERS, COURSE2_USERS, COURSE1_GRADERS, COURSE1_STUDENTS,\
    COURSE1_INSTRUCTORS
from chisubmit.client.exceptions import UnknownObjectException

class CoursePersonTests(ChisubmitClientLibsTests):
    
    fixtures = ['users', 'complete_course1']
    
    def test_get_instructors(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        instructors = course.get_instructors()
        
        self.assertEquals(len(instructors), len(COURSE1_INSTRUCTORS))
        self.assertItemsEqual([i.username for i in instructors], COURSE1_INSTRUCTORS)
        
    def test_get_graders(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        graders = course.get_graders()
        
        self.assertEquals(len(graders), len(COURSE1_GRADERS))
        self.assertItemsEqual([g.username for g in graders], COURSE1_GRADERS)
                
    def test_get_students(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        students = course.get_students()
        
        self.assertEquals(len(students), len(COURSE1_STUDENTS))
        self.assertItemsEqual([s.username for s in students], COURSE1_STUDENTS)         
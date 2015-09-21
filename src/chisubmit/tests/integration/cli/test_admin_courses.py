from chisubmit.tests.common import cli_test, ChisubmitCLITestClient, ChisubmitCLITestCase,\
    COURSE1_ID, COURSE1_NAME, COURSE2_ID, COURSE2_NAME
from chisubmit.backend.api.models import Course, Student, TeamMember
from django.contrib.auth.models import User

class CLIAdminCourse(ChisubmitCLITestCase):
            
    fixtures = ['admin_user']
            
    @cli_test
    def test_admin_course_add(self, runner):
        
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        course_id = u"cmsc12300"
        course_name = u"Foobarmentals of Foobar"
        
        result = admin.run("admin course add", [course_id, course_name])
        self.assertEquals(result.exit_code, 0)
        
        try:
            course_obj = Course.objects.get(course_id=course_id)
        except Course.DoesNotExist:
            self.fail("Course was not added to database")  
            
        self.assertEquals(course_obj.course_id, course_id)                  
        self.assertEquals(course_obj.name, course_name) 
           
        
class CLIAdminCourseExisting(ChisubmitCLITestCase):
    
    fixtures = ['admin_user', 'course1', 'course2']    
        
    @cli_test
    def test_admin_course_list(self, runner):
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        result = admin.run("admin course list")

        self.assertEquals(result.exit_code, 0)

        for val in [COURSE1_ID, COURSE1_NAME, COURSE2_ID, COURSE2_NAME]:            
            self.assertIn(val, result.output)

class CLIAdminCourseLoadUsers(ChisubmitCLITestCase):
    
    fixtures = ['admin_user', 'course1',  'course2']
             
    def gen_students(self, usernames):
        return {u: ("f"+u, "l"+u, u+"@example.org") for u in usernames}
    
    def gen_csv(self, students, filename):
        header = "username,first,last,email\n"
        rows = ["%s,%s,%s,%s" % (username, u[0], u[1], u[2]) for username, u in students.items()]
        rows.sort()
        rows = "\n".join(rows)
        
        with open(filename, "w") as f:
            f.write(header)
            f.write(rows)                 
                        
    @cli_test
    def test_admin_course_load_students(self, runner):
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        students = self.gen_students(["student1", "student2", "student3", "student4"])
        csv_file = "students.csv"
        self.gen_csv(students, csv_file)
        
        result = admin.run("admin course load-users",
                           [COURSE1_ID, csv_file, "username", "first", "last", "email", "--user-type", "student"])
        self.assertEquals(result.exit_code, 0)

        user_objs = User.objects.all()
        student_objs = Student.objects.filter(course__course_id = COURSE1_ID)

        self.assertEquals(len(user_objs), len(students) + 1)
        self.assertEquals(len(student_objs), len(students))

        
    @cli_test
    def test_admin_course_load_students_twice(self, runner):
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        students = self.gen_students(["student1", "student2", "student3", "student4"])
        csv_file = "students.csv"
        self.gen_csv(students, csv_file)
        
        result = admin.run("admin course load-users",
                           [COURSE1_ID, csv_file, "username", "first", "last", "email", "--user-type", "student"])        
        self.assertEquals(result.exit_code, 0)

        user_objs = User.objects.all()
        student_objs = Student.objects.filter(course__course_id = COURSE1_ID)

        self.assertEquals(len(user_objs), len(students) + 1)
        self.assertEquals(len(student_objs), len(students))

        result = admin.run("admin course load-users",
                           [COURSE1_ID, csv_file, "username", "first", "last", "email", "--user-type", "student"])        
        self.assertEquals(result.exit_code, 0)

        user_objs = User.objects.all()
        student_objs = Student.objects.filter(course__course_id = COURSE1_ID)

        self.assertEquals(len(user_objs), len(students) + 1)
        self.assertEquals(len(student_objs), len(students))
                
    @cli_test
    def test_admin_course_load_students_and_add(self, runner):
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        students = self.gen_students(["student1", "student2", "student3", "student4"])
        csv_file = "students.csv"
        self.gen_csv(students, csv_file)
        
        result = admin.run("admin course load-users",
                           [COURSE1_ID, csv_file, "username", "first", "last", "email", "--user-type", "student"])        
        self.assertEquals(result.exit_code, 0)

        user_objs = User.objects.all()
        student_objs = Student.objects.filter(course__course_id = COURSE1_ID)

        self.assertEquals(len(user_objs), len(students) + 1)
        self.assertEquals(len(student_objs), len(students))

        students.update(self.gen_students(["student5"]))
        self.gen_csv(students, csv_file)

        result = admin.run("admin course load-users",
                           [COURSE1_ID, csv_file, "username", "first", "last", "email", "--user-type", "student"])        
        self.assertEquals(result.exit_code, 0)

        user_objs = User.objects.all()
        student_objs = Student.objects.filter(course__course_id = COURSE1_ID)

        self.assertEquals(len(user_objs), len(students) + 1)
        self.assertEquals(len(student_objs), len(students))
        
    @cli_test
    def test_admin_course_load_students_and_drop(self, runner):
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        students = self.gen_students(["student1", "student2", "student3", "student4"])
        csv_file = "students.csv"
        self.gen_csv(students, csv_file)
        
        result = admin.run("admin course load-users",
                           [COURSE1_ID, csv_file, "username", "first", "last", "email", "--user-type", "student"])        
        self.assertEquals(result.exit_code, 0)

        user_objs = User.objects.all()
        student_objs = Student.objects.filter(course__course_id = COURSE1_ID)

        self.assertEquals(len(user_objs), len(students) + 1)
        self.assertEquals(len(student_objs), len(students))

        del students["student3"]
        self.gen_csv(students, csv_file)

        result = admin.run("admin course load-users",
                           [COURSE1_ID, csv_file, "username", "first", "last", "email", "--user-type", "student", "--sync"])        
        self.assertEquals(result.exit_code, 0)

        user_objs = User.objects.all()
        student_objs = Student.objects.filter(course__course_id = COURSE1_ID, dropped = False)

        self.assertEquals(len(user_objs), len(students) + 2)
        self.assertEquals(len(student_objs), len(students))        
        
        
    @cli_test
    def test_admin_course_load_students_two(self, runner):
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        students1 = self.gen_students(["student1", "student2", "student3", "student4"])
        csv_file1 = "course1.csv"
        self.gen_csv(students1, csv_file1)
        
        result = admin.run("admin course load-users",
                           [COURSE1_ID, csv_file1, "username", "first", "last", "email", "--user-type", "student"])        
        self.assertEquals(result.exit_code, 0)

        user_objs = User.objects.all()
        student_objs = Student.objects.filter(course__course_id = COURSE1_ID)

        self.assertEquals(len(user_objs), len(students1) + 1)
        self.assertEquals(len(student_objs), len(students1))

        students2 = self.gen_students(["student3", "student4", "student5", "student6"])
        csv_file2 = "course2.csv"
        self.gen_csv(students2, csv_file2)
        
        result = admin.run("admin course load-users",
                           [COURSE2_ID, csv_file2, "username", "first", "last", "email", "--user-type", "student"])        
        self.assertEquals(result.exit_code, 0)

        user_objs = User.objects.all()
        student_objs = Student.objects.filter(course__course_id = COURSE2_ID)

        self.assertEquals(len(user_objs), 6 + 1)
        self.assertEquals(len(student_objs), len(students2))
             
          
class CLIAdminCourseCreateRepos(ChisubmitCLITestCase):
    
    fixtures = ['users', 'course1',  'course1_users', 'course1_teams']            
    
    def setup_git_testing(self, course_id):
        try:
            course_obj = Course.objects.get(course_id=course_id)
        except Course.DoesNotExist:
            self.fail("Course %s not in database" % course_id)
            
        course_obj.git_server_connstr = "server_type=Testing;local_path=./test-fs/server"
        course_obj.git_staging_connstr = "server_type=Testing;local_path=./test-fs/staging"
        course_obj.save()
    
    @cli_test
    def test_admin_course_create_repos(self, runner):
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        self.setup_git_testing(COURSE1_ID)
        
        result = admin.run("admin course create-repos", [COURSE1_ID])          
        self.assertEquals(result.exit_code, 0)
        
    @cli_test
    def test_admin_course_create_repos_twice(self, runner):
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        self.setup_git_testing(COURSE1_ID)
        
        result = admin.run("admin course create-repos", [COURSE1_ID])          
        self.assertEquals(result.exit_code, 0)        

        result = admin.run("admin course create-repos", [COURSE1_ID])          
        self.assertEquals(result.exit_code, 0)        

    @cli_test
    def test_admin_course_create_repos_incomplete_registration(self, runner):
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        self.setup_git_testing(COURSE1_ID)
        
        tm = TeamMember.objects.get(team__team_id="student1-student2", student__user__username="student2")
        tm.confirmed = False
        tm.save()
        
        result = admin.run("admin course create-repos", [COURSE1_ID])          
        self.assertEquals(result.exit_code, 0)

        tm.confirmed = True
        tm.save()

        result = admin.run("admin course create-repos", [COURSE1_ID])          
        self.assertEquals(result.exit_code, 0)
    
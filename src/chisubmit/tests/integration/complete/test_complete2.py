from chisubmit.tests.common import cli_test, ChisubmitCLITestCase
from chisubmit.common.utils import get_datetime_now_utc
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

from datetime import timedelta
from chisubmit.backend.api.models import Course, get_user_by_username

class CLICompleteWorkflowExtensionsPerStudent(ChisubmitCLITestCase):
        
    fixtures = ['admin_user']
    
    @cli_test
    def test_complete_with_extensions_per_student(self, runner):
        course_id = u"cmsc40300"
        course_name = u"Foobarmentals of Foobar II"

        admin_id = u"admin"
        instructor_ids = [u"instructor"]
        grader_ids= [u"grader"]
        student_ids = [u"student1", u"student2", u"student3", u"student4"]
        
        all_users = instructor_ids + grader_ids + student_ids
        
        admin, instructors, graders, students = self.create_clients(runner, admin_id, instructor_ids, grader_ids, student_ids, course_id, verbose = True)
        self.create_users(admin, all_users)
                
        self.create_course(admin, course_id, course_name)

        course = Course.get_by_course_id(course_id)
        self.assertIsNotNone(course)
        self.assertEquals(course.name, course_name)

        result = admin.run("admin course set-attribute %s default_extensions 3" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        result = admin.run("admin course set-attribute %s extension_policy per-student" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        self.add_users_to_course(admin, course_id, instructors, graders, students)
        
        deadline = get_datetime_now_utc() - timedelta(hours=23)
        deadline = deadline.replace(tzinfo=None).isoformat(sep=" ")        

        result = instructors[0].run("instructor assignment add", 
                                    ["pa1", "Programming Assignment 1", deadline])
        self.assertEquals(result.exit_code, 0)

        result = instructors[0].run("instructor assignment set-attribute", 
                                    ["pa1", "max_students", "2"])
        self.assertEquals(result.exit_code, 0)

        deadline = get_datetime_now_utc() - timedelta(hours=47)
        deadline = deadline.isoformat(sep=" ")

        result = instructors[0].run("instructor assignment add", 
                                    ["pa2", "Programming Assignment 2", deadline])
        self.assertEquals(result.exit_code, 0)

        result = instructors[0].run("instructor assignment set-attribute", 
                                    ["pa2", "max_students", "2"])
        self.assertEquals(result.exit_code, 0)

        deadline = get_datetime_now_utc() - timedelta(hours=47)
        deadline = deadline.isoformat(sep=" ")

        result = instructors[0].run("instructor assignment add", 
                                    ["pa3", "Programming Assignment 3", deadline])
        self.assertEquals(result.exit_code, 0)

        result = instructors[0].run("instructor assignment set-attribute", 
                                    ["pa3", "max_students", "2"])
        self.assertEquals(result.exit_code, 0)

        deadline = get_datetime_now_utc() - timedelta(hours=23)
        deadline = deadline.replace(tzinfo=None).isoformat(sep=" ")        

        result = instructors[0].run("instructor assignment add", 
                                    ["pa4", "Programming Assignment 4", deadline])
        self.assertEquals(result.exit_code, 0)

        result = instructors[0].run("instructor assignment set-attribute", 
                                    ["pa4", "max_students", "2"])
        self.assertEquals(result.exit_code, 0)

        deadline = get_datetime_now_utc() + timedelta(hours=2)
        deadline = deadline.replace(tzinfo=None).isoformat(sep=" ")        

        result = instructors[0].run("instructor assignment add", 
                                    ["pa5", "Programming Assignment 5", deadline])
        self.assertEquals(result.exit_code, 0)

        result = instructors[0].run("instructor assignment set-attribute", 
                                    ["pa5", "max_students", "2"])
        self.assertEquals(result.exit_code, 0)
        
        
        teams = [u"student1-student2", 
                 u"student3-student4",
                 u"student1-student3",
                 u"student2-student4"]        

        students_team = [ (students[0], students[1]),
                          (students[2], students[3]),
                          (students[0], students[2]),
                          (students[1], students[3])]
        

        self.register_team(students_team[0], teams[0], "pa1", course_id)
        self.register_team(students_team[1], teams[1], "pa2", course_id)
        
        team_git_paths, team_git_repos, team_commits = self.create_team_repos(admin, course_id, teams[0:2], students_team[0:2])

        self.register_team(students_team[2], teams[2], "pa3", course_id)
        self.register_team(students_team[2], teams[2], "pa4", course_id)
        self.register_team(students_team[2], teams[2], "pa5", course_id)
        self.register_team(students_team[3], teams[3], "pa3", course_id)
        self.register_team(students_team[3], teams[3], "pa4", course_id)
        self.register_team(students_team[3], teams[3], "pa5", course_id)
        
        x, y, z = self.create_team_repos(admin, course_id, teams[2:4], students_team[2:4])
        
        team_git_paths += x
        team_git_repos += y
        team_commits += z
        
        # Team 0 submits with one extension to pa1
        # Student 0 and 1 now have 2 extensions left each
        result = students_team[0][0].run("student assignment submit", 
                                         [teams[0], "pa1", team_commits[0][0].hexsha, 
                                          "--extensions", "1",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)
        
        s1 = course.get_student(get_user_by_username(students_team[0][0].user_id))
        s2 = course.get_student(get_user_by_username(students_team[0][1].user_id))
        t = course.get_team(teams[0])
        
        self.assertEqual(t.get_extensions_available(), 2)
        self.assertEqual(s1.get_extensions_available(), 2)
        self.assertEqual(s2.get_extensions_available(), 2)
        
        # Team 1 submits with two extensions to pa2
        # Student 2 and 3 now have 1 extension left each
        result = students_team[1][0].run("student assignment submit", 
                                         [teams[1], "pa2", team_commits[1][0].hexsha, 
                                          "--extensions", "2",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        s1 = course.get_student(get_user_by_username(students_team[1][0].user_id))
        s2 = course.get_student(get_user_by_username(students_team[1][1].user_id))
        t = course.get_team(teams[1])
        
        self.assertEqual(t.get_extensions_available(), 1)
        self.assertEqual(s1.get_extensions_available(), 1)
        self.assertEqual(s2.get_extensions_available(), 1)

        result = students_team[0][0].run("student team show", [teams[0]])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        result = students_team[1][0].run("student team show", [teams[1]])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)


        # Now we have two new teams:
        #
        # Team 2 with Student 0 and 2, with 2 and 1 extensions left respectively.
        # This team can only submit to projects requiring one extension
        # 
        # Team 3 with Student 1 and 3, with 2 and 1 extensions left respectively.
        # This team can only submit to projects requiring one extension

        # Team 2 tries to submit to pa3 with one extension (one less than needed)
        # and is denied
        result = students_team[2][0].run("student assignment submit", 
                                         [teams[2], "pa3", team_commits[2][0].hexsha, 
                                          "--extensions", "1",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)

        s1 = course.get_student(get_user_by_username(students_team[2][0].user_id))
        s2 = course.get_student(get_user_by_username(students_team[2][1].user_id))
        t = course.get_team(teams[2])
        
        self.assertEqual(t.get_extensions_available(), 1)
        self.assertEqual(s1.get_extensions_available(), 2)
        self.assertEqual(s2.get_extensions_available(), 1)


        # Team 2 tries to submit to pa3 with two extensions (the right number,
        # but not enough because one of the students only has one extension left)
        # and is denied
        result = students_team[2][0].run("student assignment submit", 
                                         [teams[2], "pa3", team_commits[2][0].hexsha, 
                                          "--extensions", "2",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)

        s1 = course.get_student(get_user_by_username(students_team[2][0].user_id))
        s2 = course.get_student(get_user_by_username(students_team[2][1].user_id))
        t = course.get_team(teams[2])
        
        self.assertEqual(t.get_extensions_available(), 1)
        self.assertEqual(s1.get_extensions_available(), 2)
        self.assertEqual(s2.get_extensions_available(), 1)


        # Team 2 tries submitting to pa4 with zero extensions (one less than needed)
        # and is denied
        result = students_team[2][0].run("student assignment submit", 
                                         [teams[2], "pa4", team_commits[2][1].hexsha, 
                                          "--extensions", "0",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)

        s1 = course.get_student(get_user_by_username(students_team[2][0].user_id))
        s2 = course.get_student(get_user_by_username(students_team[2][1].user_id))
        t = course.get_team(teams[2])
        
        self.assertEqual(t.get_extensions_available(), 1)
        self.assertEqual(s1.get_extensions_available(), 2)
        self.assertEqual(s2.get_extensions_available(), 1)


        # Team 2 tries submitting to pa4 with one extension (the correct number)
        # and it goes through
        result = students_team[2][0].run("student assignment submit", 
                                         [teams[2], "pa4", team_commits[2][1].hexsha, 
                                          "--extensions", "1",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        s1 = course.get_student(get_user_by_username(students_team[2][0].user_id))
        s2 = course.get_student(get_user_by_username(students_team[2][1].user_id))
        t = course.get_team(teams[2])
        
        self.assertEqual(t.get_extensions_available(), 0)
        self.assertEqual(s1.get_extensions_available(), 1)
        self.assertEqual(s2.get_extensions_available(), 0)
                        

        # Team 2 tries submitting to pa5 with zero extensions and is accepted
        result = students_team[2][0].run("student assignment submit", 
                                         [teams[2], "pa5", team_commits[2][1].hexsha, 
                                          "--extensions", "0",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)
                        
        s1 = course.get_student(get_user_by_username(students_team[2][0].user_id))
        s2 = course.get_student(get_user_by_username(students_team[2][1].user_id))
        t = course.get_team(teams[2])
        
        self.assertEqual(t.get_extensions_available(), 0)
        self.assertEqual(s1.get_extensions_available(), 1)
        self.assertEqual(s2.get_extensions_available(), 0)
                        

        # Team 3 tries submitting to pa5 with zero extensions and is accepted
        result = students_team[3][0].run("student assignment submit", 
                                         [teams[3], "pa5", team_commits[3][1].hexsha, 
                                          "--extensions", "0",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        s1 = course.get_student(get_user_by_username(students_team[3][0].user_id))
        s2 = course.get_student(get_user_by_username(students_team[3][1].user_id))
        t = course.get_team(teams[3])
        
        self.assertEqual(t.get_extensions_available(), 1)
        self.assertEqual(s1.get_extensions_available(), 2)
        self.assertEqual(s2.get_extensions_available(), 1)

        for team, student_team in zip(teams, students_team):
            result = student_team[0].run("student team show", [team])
            self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        
        

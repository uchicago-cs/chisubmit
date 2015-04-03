from chisubmit.tests.common import cli_test, ChisubmitIntegrationTestCase
from chisubmit.common.utils import get_datetime_now_utc
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

from datetime import timedelta

class CLICompleteWorkflowExtensionsPerStudent(ChisubmitIntegrationTestCase):
            
    @cli_test
    def test_complete_with_extensions_per_student(self, runner):
        from chisubmit.backend.webapp.api.teams.models import Team
        from chisubmit.backend.webapp.api.courses.models import CoursesStudents

        course_id = u"cmsc40300"
        course_name = u"Foobarmentals of Foobar II"

        admin_id = u"admin"
        instructor_ids = [u"instructor"]
        grader_ids= [u"grader"]
        student_ids = [u"student1", u"student2", u"student3", u"student4"]
        
        all_users = instructor_ids + grader_ids + student_ids
        
        admin, instructors, graders, students = self.create_clients(runner, course_id, admin_id, instructor_ids, grader_ids, student_ids)
        self.create_users(admin, all_users)
        
        self.create_course(admin, course_id, course_name)

        result = admin.run("admin course set-option %s default-extensions 3" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        result = admin.run("admin course set-option %s extension-policy per_student" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        self.add_users_to_course(admin, course_id, instructors, graders, students)
        
        deadline = get_datetime_now_utc() - timedelta(hours=23)
        deadline = deadline.replace(tzinfo=None).isoformat(sep=" ")        

        result = instructors[0].run("instructor assignment add", 
                                    ["pa1", "Programming Assignment 1", deadline])
        self.assertEquals(result.exit_code, 0)

        deadline = get_datetime_now_utc() - timedelta(hours=47)
        deadline = deadline.isoformat(sep=" ")

        result = instructors[0].run("instructor assignment add", 
                                    ["pa2", "Programming Assignment 2", deadline])
        self.assertEquals(result.exit_code, 0)

        deadline = get_datetime_now_utc() - timedelta(hours=47)
        deadline = deadline.isoformat(sep=" ")

        result = instructors[0].run("instructor assignment add", 
                                    ["pa3", "Programming Assignment 3", deadline])
        self.assertEquals(result.exit_code, 0)

        deadline = get_datetime_now_utc() - timedelta(hours=23)
        deadline = deadline.replace(tzinfo=None).isoformat(sep=" ")        

        result = instructors[0].run("instructor assignment add", 
                                    ["pa4", "Programming Assignment 4", deadline])
        self.assertEquals(result.exit_code, 0)

        deadline = get_datetime_now_utc() + timedelta(hours=2)
        deadline = deadline.replace(tzinfo=None).isoformat(sep=" ")        

        result = instructors[0].run("instructor assignment add", 
                                    ["pa5", "Programming Assignment 5", deadline])
        self.assertEquals(result.exit_code, 0)
        
        
        teams = [u"the-flaming-foobars", 
                 u"the-magnificent-mallocs",
                 u"the-reticent-reallocs",
                 u"the-panicked-printfs"]        

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
        
        cs1 =  CoursesStudents.from_id(course_id, students_team[0][0].user_id)
        cs2 =  CoursesStudents.from_id(course_id, students_team[0][1].user_id)
        t = Team.from_id(course_id, teams[0])
        
        self.assertEqual(t.get_extensions_available("per_student"), 2)
        self.assertEqual(cs1.get_extensions_available(), 2)
        self.assertEqual(cs2.get_extensions_available(), 2)
        
        # Team 1 submits with two extensions to pa2
        # Student 2 and 3 now have 1 extension left each
        result = students_team[1][0].run("student assignment submit", 
                                         [teams[1], "pa2", team_commits[1][0].hexsha, 
                                          "--extensions", "2",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        cs1 =  CoursesStudents.from_id(course_id, students_team[1][0].user_id)
        cs2 =  CoursesStudents.from_id(course_id, students_team[1][1].user_id)
        t = Team.from_id(course_id, teams[1])
        
        self.assertEqual(t.get_extensions_available("per_student"), 1)
        self.assertEqual(cs1.get_extensions_available(), 1)
        self.assertEqual(cs2.get_extensions_available(), 1)

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

        cs1 =  CoursesStudents.from_id(course_id, students_team[2][0].user_id)
        cs2 =  CoursesStudents.from_id(course_id, students_team[2][1].user_id)
        t = Team.from_id(course_id, teams[2])
        
        self.assertEqual(t.get_extensions_available("per_student"), 1)
        self.assertEqual(cs1.get_extensions_available(), 2)
        self.assertEqual(cs2.get_extensions_available(), 1)


        # Team 2 tries to submit to pa3 with two extensions (the right number,
        # but not enough because one of the students only has one extension left)
        # and is denied
        result = students_team[2][0].run("student assignment submit", 
                                         [teams[2], "pa3", team_commits[2][0].hexsha, 
                                          "--extensions", "2",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)

        cs1 =  CoursesStudents.from_id(course_id, students_team[2][0].user_id)
        cs2 =  CoursesStudents.from_id(course_id, students_team[2][1].user_id)
        t = Team.from_id(course_id, teams[2])
        
        self.assertEqual(t.get_extensions_available("per_student"), 1)
        self.assertEqual(cs1.get_extensions_available(), 2)
        self.assertEqual(cs2.get_extensions_available(), 1)


        # Team 2 tries submitting to pa4 with zero extensions (one less than needed)
        # and is denied
        result = students_team[2][0].run("student assignment submit", 
                                         [teams[2], "pa4", team_commits[2][1].hexsha, 
                                          "--extensions", "0",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)

        cs1 =  CoursesStudents.from_id(course_id, students_team[2][0].user_id)
        cs2 =  CoursesStudents.from_id(course_id, students_team[2][1].user_id)
        t = Team.from_id(course_id, teams[2])
        
        self.assertEqual(t.get_extensions_available("per_student"), 1)
        self.assertEqual(cs1.get_extensions_available(), 2)
        self.assertEqual(cs2.get_extensions_available(), 1)

        # Team 2 tries submitting to pa4 with one extension (the correct number)
        # and it goes through
        result = students_team[2][0].run("student assignment submit", 
                                         [teams[2], "pa4", team_commits[2][1].hexsha, 
                                          "--extensions", "1",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)
                        
        cs1 =  CoursesStudents.from_id(course_id, students_team[2][0].user_id)
        cs2 =  CoursesStudents.from_id(course_id, students_team[2][1].user_id)
        t = Team.from_id(course_id, teams[2])
        
        self.assertEqual(t.get_extensions_available("per_student"), 0)
        self.assertEqual(cs1.get_extensions_available(), 1)
        self.assertEqual(cs2.get_extensions_available(), 0)


        # Team 2 tries submitting to pa5 with zero extensions and is accepted
        result = students_team[2][0].run("student assignment submit", 
                                         [teams[2], "pa5", team_commits[2][1].hexsha, 
                                          "--extensions", "0",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)
                        
        cs1 =  CoursesStudents.from_id(course_id, students_team[2][0].user_id)
        cs2 =  CoursesStudents.from_id(course_id, students_team[2][1].user_id)
        t = Team.from_id(course_id, teams[2])
        
        self.assertEqual(t.get_extensions_available("per_student"), 0)
        self.assertEqual(cs1.get_extensions_available(), 1)
        self.assertEqual(cs2.get_extensions_available(), 0)


        # Team 3 tries submitting to pa5 with zero extensions and is accepted
        result = students_team[3][0].run("student assignment submit", 
                                         [teams[3], "pa5", team_commits[3][1].hexsha, 
                                          "--extensions", "0",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)
                        
        cs1 =  CoursesStudents.from_id(course_id, students_team[3][0].user_id)
        cs2 =  CoursesStudents.from_id(course_id, students_team[3][1].user_id)
        t = Team.from_id(course_id, teams[3])
        
        self.assertEqual(t.get_extensions_available("per_student"), 1)
        self.assertEqual(cs1.get_extensions_available(), 2)
        self.assertEqual(cs2.get_extensions_available(), 1)


        for team, student_team in zip(teams, students_team):
            result = student_team[0].run("student team show", [team])
            self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        
        

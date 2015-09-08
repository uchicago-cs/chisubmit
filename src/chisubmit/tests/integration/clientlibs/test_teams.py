from chisubmit.tests.integration.clientlibs import ChisubmitClientLibsTestCase
from chisubmit.tests.common import COURSE1_ASSIGNMENTS, COURSE2_ASSIGNMENTS,\
    COURSE1_TEAMS, COURSE1_TEAM_MEMBERS
from chisubmit.client.exceptions import BadRequestException
from chisubmit.backend.api.models import Course, Assignment, TeamMember,\
    Registration, Submission, Grade

class TeamTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams']
    
    def test_get_teams(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        teams = course.get_teams()
        
        self.assertEquals(len(teams), len(COURSE1_TEAMS))
        self.assertItemsEqual([t.team_id for t in teams], COURSE1_TEAMS)
        
    def test_get_team(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for team_name in COURSE1_TEAMS:
            team = course.get_team(team_name)
            
            self.assertEquals(team.team_id, team_name)
            
    def test_create_team(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        team = course.create_team(team_id = "student2-student3",
                                  extensions = 2,
                                  active = False)
        self.assertEquals(team.team_id, "student2-student3")
        self.assertEquals(team.extensions, 2)
        self.assertEquals(team.active, False)
        
        course_obj = Course.get_by_course_id("cmsc40100")
        self.assertIsNotNone(course_obj)
        
        team_obj = course_obj.get_team("student2-student3")
        self.assertIsNotNone(team_obj, "Team was not added to database")
            
        self.assertEquals(team_obj.team_id, "student2-student3")                  
        self.assertEquals(team_obj.extensions, 2)                  
        self.assertEquals(team_obj.active, False)                  
                    
class TeamMemberTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams']
    
    def test_get_team_members(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            team_members = team.get_team_members()
            
            self.assertEquals(len(team_members), len(COURSE1_TEAM_MEMBERS[t]))
            self.assertItemsEqual([tm.username for tm in team_members], COURSE1_TEAM_MEMBERS[t])
            self.assertItemsEqual([tm.student.user.username for tm in team_members], COURSE1_TEAM_MEMBERS[t])
        
    def test_get_team_member(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            
            for tm in COURSE1_TEAM_MEMBERS[t]:
                team_member = team.get_team_member(tm)
                
                self.assertEqual(team_member.username, tm)
                self.assertEqual(team_member.student.user.username, tm)
                self.assertEqual(team_member.confirmed, True)
                
    
    def test_create_team_with_team_members(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        team = course.create_team(team_id = "student2-student3",
                                  extensions = 2,
                                  active = False)
        self.assertEquals(team.team_id, "student2-student3")
        self.assertEquals(team.extensions, 2)
        self.assertEquals(team.active, False)
        
        course_obj = Course.get_by_course_id("cmsc40100")
        self.assertIsNotNone(course_obj)
        
        team_obj = course_obj.get_team("student2-student3")
        self.assertIsNotNone(team_obj, "Team was not added to database")
            
        self.assertEquals(team_obj.team_id, "student2-student3")                  
        self.assertEquals(team_obj.extensions, 2)                  
        self.assertEquals(team_obj.active, False)
              
        team_member = team.add_team_member("student2", confirmed = False)
        self.assertEqual(team_member.username, "student2")
        self.assertEqual(team_member.student.user.username, "student2")
        self.assertEqual(team_member.confirmed, False)
                
        team_member_objs = TeamMember.objects.filter(team = team_obj, student__user__username = "student2")
        self.assertEquals(len(team_member_objs), 1)
        team_member_obj = team_member_objs[0]
        self.assertEqual(team_member_obj.student.user.username, "student2")
        self.assertEqual(team_member_obj.confirmed, False)
        
        team.add_team_member("student3", confirmed = True)
        team_member_objs = TeamMember.objects.filter(team = team_obj, student__user__username = "student3")
        self.assertEquals(len(team_member_objs), 1)
        team_member_obj = team_member_objs[0]
        self.assertEqual(team_member_obj.student.user.username, "student3")
        self.assertEqual(team_member_obj.confirmed, True)

        team_members = team.get_team_members()
        
        self.assertEquals(len(team_members), 2)
        self.assertItemsEqual([tm.username for tm in team_members], ["student2","student3"])
        self.assertItemsEqual([tm.student.user.username for tm in team_members], ["student2","student3"])        
        
class RegistrationTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                         'course1_pa1', 'course1_pa1_registrations',
                         'course1_pa2']    
    
    def test_get_registrations(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            registrations = team.get_assignment_registrations()
            
            self.assertEquals(len(registrations), 1)
            self.assertItemsEqual([r.assignment_id for r in registrations], ["pa1"])
            self.assertItemsEqual([r.assignment.assignment_id for r in registrations], ["pa1"])
        
    def test_get_registration(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            registration = team.get_assignment_registration("pa1")

            self.assertEqual(registration.assignment_id, "pa1")
            self.assertEqual(registration.assignment.assignment_id, "pa1")
            self.assertEqual(registration.grader_username, None)
            self.assertEqual(registration.grader, None)
            
    def test_create_registration(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            registration = team.add_assignment_registration("pa2")

            self.assertEqual(registration.assignment_id, "pa2")
            self.assertEqual(registration.assignment.assignment_id, "pa2")
            self.assertEqual(registration.grader_username, None)
            self.assertEqual(registration.grader, None)   
            
            registration_objs = Registration.objects.filter(team__team_id = t, assignment__assignment_id = "pa2")
            self.assertEquals(len(registration_objs), 1)
            registration_obj = registration_objs[0]
            self.assertEqual(registration_obj.team.team_id, t)
            self.assertEqual(registration_obj.assignment.assignment_id, "pa2")
            self.assertIsNone(registration_obj.grader)            
            
            registrations = team.get_assignment_registrations()
            
            self.assertEquals(len(registrations), 2)
            self.assertItemsEqual([r.assignment_id for r in registrations], ["pa1", "pa2"])
            self.assertItemsEqual([r.assignment.assignment_id for r in registrations], ["pa1", "pa2"])
            
class SubmissionTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                         'course1_pa1', 'course1_pa1_registrations_with_submissions',
                         'course1_pa2']
            
    def test_get_submissions(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        team = course.get_team("student1-student2")
        registration = team.get_assignment_registration("pa1")
        submissions = registration.get_submissions()
            
        self.assertEquals(len(submissions), 2)
        self.assertIn(registration.final_submission_id, [s.id for s in submissions])

        team = course.get_team("student3-student4")
        registration = team.get_assignment_registration("pa1")
        submissions = registration.get_submissions()
            
        self.assertEquals(len(submissions), 1)
        self.assertEquals(submissions[0].id, registration.final_submission_id)
        
    def test_get_submission(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            registration = team.get_assignment_registration("pa1")
            final_submission_id = registration.final_submission_id
            submission = registration.get_submission(final_submission_id)

            self.assertEqual(submission.id, final_submission_id)
            
    def test_create_submission(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            registration = team.get_assignment_registration("pa1")
            submissions = registration.get_submissions()
            n_submissions = len(submissions)
            
            sha = "COMMITSHA" + team.team_id
            submission = registration.add_submission(sha, 42)

            self.assertEqual(submission.extensions_used, 42)
            self.assertEqual(submission.commit_sha, sha)
            
            submission_objs = Submission.objects.filter(pk = submission.id)
            self.assertEquals(len(submission_objs), 1)
            submission_obj = submission_objs[0]
            self.assertEqual(submission_obj.extensions_used, 42)
            self.assertEqual(submission_obj.commit_sha, sha)
            
            submissions = registration.get_submissions()
            self.assertEquals(len(submissions), n_submissions + 1)
            
            
class GradeTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                         'course1_pa1', 'course1_pa1_registrations',
                         'course1_pa2']    
            
    def test_create_grade(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")

        assignment = course.get_assignment("pa1")
        rubric_components = assignment.get_rubric_components()
        
        points = 10
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            registration = team.get_assignment_registration("pa1")
            
            for rc in rubric_components:
                grade = registration.add_grade(rc, points = points)

                self.assertEqual(grade.points, points)
                self.assertEqual(grade.rubric_component.description, rc.description)
                registration_obj = Registration.objects.get(team__team_id = team.team_id, assignment__assignment_id = "pa1")
                grade_objs = Grade.objects.filter(registration = registration_obj, rubric_component_id = rc.id)
                self.assertEquals(len(grade_objs), 1)
                grade_obj = grade_objs[0]
                self.assertEqual(grade_obj.points, points)
                
                points += 5
                
            
class ExistingGradeTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                     'course1_pa1', 'course1_pa1_registrations', 'course1_pa1_grades',
                     'course1_pa2']
            
    def test_get_grades(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        assignment = course.get_assignment("pa1")
        rubric_components = assignment.get_rubric_components()
        rubric_components_descriptions = [rc.description for rc in rubric_components]
        
        for t in COURSE1_TEAMS:        
            team = course.get_team(t)
            registration = team.get_assignment_registration("pa1")
            grades = registration.get_grades()
            
            self.assertEquals(len(grades), 2)
            self.assertItemsEqual([g.rubric_component.description for g in grades], rubric_components_descriptions)
        
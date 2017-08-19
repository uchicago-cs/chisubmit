from chisubmit.tests.common import cli_test, ChisubmitCLITestCase
from chisubmit.common.utils import get_datetime_now_utc, convert_datetime_to_local,\
    set_testing_now
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

from datetime import timedelta
import os

class CLICompleteWorkflowMultipleInstructorsMultipleGraders(ChisubmitCLITestCase):
        
    fixtures = ['admin_user']
        
    @cli_test
    def test_complete_with_multiple_instructors_multiple_graders(self, runner):
        course_id = u"cmsc40200"
        course_name = u"Foobarmentals of Foobar"

        admin_id = u"admin"
        instructor_ids = [u"instructor1", u"instructor2"]
        grader_ids= [u"grader1", u"grader2"]
        student_ids = [u"student1", u"student2", u"student3", u"student4"]
                
        all_users = instructor_ids + grader_ids + student_ids
        
        admin, instructors, graders, students = self.create_clients(runner, admin_id, instructor_ids, grader_ids, student_ids, course_id, verbose = True)
        self.create_users(admin, all_users)
        
        self.create_course(admin, course_id, course_name)
        
        self.add_users_to_course(admin, course_id, instructors, graders, students)
        
        students_team = [[s] for s in students]
                
        deadline = get_datetime_now_utc() + timedelta(hours=1)
        deadline = convert_datetime_to_local(deadline)
        deadline = deadline.replace(tzinfo=None).isoformat(sep=" ")        

        result = instructors[0].run("instructor assignment add", 
                                    ["pa1", "Programming Assignment 1", deadline])
        self.assertEquals(result.exit_code, 0)        

        pa1_rubric = """Points:
    - The PA1 Tests:
        Points Possible: 50
        Points Obtained: 

    - The PA1 Design:
        Points Possible: 50
        Points Obtained: 
        
Total Points: 0 / 100
"""

        with open("pa1.rubric.txt", "w") as f:
            f.write(pa1_rubric)
            
        result = instructors[0].run("instructor assignment add-rubric", 
                                    ["pa1", "pa1.rubric.txt"])
        self.assertEquals(result.exit_code, 0)

        
        result = admin.run("admin course show", ["--include-users", "--include-assignments", course_id])
        self.assertEquals(result.exit_code, 0)

        for student_id, student in zip(student_ids, students):
            self.register_team([student], student_id, "pa1", course_id)

        for student_id, student in zip(student_ids, students):                    
            result = student.run("student team list")
            self.assertEquals(result.exit_code, 0)
            self.assertIn(student_id, result.output)
        
            result = student.run("student team show", [student_id])
            self.assertEquals(result.exit_code, 0)            

        result = instructors[0].run("instructor team list")
        self.assertEquals(result.exit_code, 0)
        
        for student_id in student_ids:
            result = instructors[0].run("instructor team show", [student_id])
            self.assertEquals(result.exit_code, 0)

        student_git_paths, student_git_repos, team_commits = self.create_team_repos(admin, course_id, student_ids, students_team)
        
        
        for student_id, student in zip(student_ids, students):   
            result = student.run("student assignment submit", 
                                             ["pa1", "--yes"])
            self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

            result = student.run("student team show", [student_id])
            self.assertEquals(result.exit_code, 0)

        # Let the deadline "pass"
        new_now = get_datetime_now_utc() + timedelta(hours=2)
        set_testing_now(new_now)

        print
        print "~~~ Time has moved 'forward' by two hours ~~~"
        print

        # The "master instructor" creates the grading repos

        result = instructors[0].run("instructor grading list-submissions", ["pa1"])
        self.assertEquals(result.exit_code, 0)

        result = instructors[0].run("instructor grading create-grading-repos", ["--master", "pa1"])
        self.assertEquals(result.exit_code, 0)        
                        
        result = instructors[0].run("instructor grading assign-grader", ["pa1", "student1", "grader1"])
        self.assertEquals(result.exit_code, 0)
        result = instructors[0].run("instructor grading assign-grader", ["pa1", "student2", "grader1"])
        self.assertEquals(result.exit_code, 0)
        result = instructors[0].run("instructor grading assign-grader", ["pa1", "student3", "grader2"])
        self.assertEquals(result.exit_code, 0)
        result = instructors[0].run("instructor grading assign-grader", ["pa1", "student4", "grader2"])
        self.assertEquals(result.exit_code, 0)
        
        result = instructors[0].run("instructor grading list-grader-assignments", ["pa1"])
        self.assertEquals(result.exit_code, 0)
        
        result = instructors[0].run("instructor grading show-grading-status", ["--by-grader", "pa1"])
        self.assertEquals(result.exit_code, 0)       
               
        result = instructors[0].run("instructor grading push-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)
        

        # The non-master instructor downloads the grading repos
        
        result = instructors[1].run("instructor grading create-grading-repos", ["pa1"])
        self.assertEquals(result.exit_code, 0)   
        
        result = instructors[1].run("instructor grading show-grading-status", ["--by-grader", "pa1"])
        self.assertEquals(result.exit_code, 0)         
        
        # Grader 1 pulls their grading
        result = graders[0].run("grader pull-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)        
                    
        student1_grading_repo_path = "chisubmit-test/repositories/%s/%s/%s" % (course_id, "pa1", "student1")
        student2_grading_repo_path = "chisubmit-test/repositories/%s/%s/%s" % (course_id, "pa1", "student2")
            
        student_git_repos[0], student_git_paths[0] = graders[0].get_local_git_repository(student1_grading_repo_path)
        student_git_repos[1], student_git_paths[1] = graders[0].get_local_git_repository(student2_grading_repo_path)
  
        student1_rubric_path = "%s/pa1.rubric.txt" % student_git_paths[0] 
        student2_rubric_path = "%s/pa1.rubric.txt" % student_git_paths[1] 


        # Grader 1 grades student1 and pushes the grading.
        
        student1_rubric = """Points:
    The PA1 Tests:
        Points Possible: 50
        Points Obtained: 45

    The PA1 Design:
        Points Possible: 50
        Points Obtained: 30
        
Penalties:
    Used O(n^156) algorithm: -10
    Submitted code in a Word document: -30

Bonuses:
    Worked alone: 15

Total Points: 50 / 100

Comments: >
    None"""

        with open(student1_rubric_path, "w") as f:
            f.write(student1_rubric)

        result = graders[0].run("grader validate-rubrics", ["pa1"])
        self.assertEquals(result.exit_code, 0)        
    
        student_git_repos[0].index.add(["pa1.rubric.txt"])
        student_git_repos[0].index.commit("Finished grading")
        
        result = graders[0].run("grader push-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)                

        # The non-master instructor pulls the repos and generates a report

        result = instructors[1].run("instructor grading pull-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)        
        
        result = instructors[1].run("instructor grading show-grading-status", ["--by-grader", "pa1"])
        self.assertEquals(result.exit_code, 0)         
        
        # Grader 1 grades student2 and pushes the grading.
        
        student2_rubric = """Points:
    The PA1 Tests:
        Points Possible: 50
        Points Obtained: 50

    The PA1 Design:
        Points Possible: 50
        Points Obtained: 45

Total Points: 95 / 100

Comments: >
    Great job!"""

        with open(student2_rubric_path, "w") as f:
            f.write(student2_rubric)

        result = graders[0].run("grader validate-rubrics", ["pa1"])
        self.assertEquals(result.exit_code, 0)        
    
        student_git_repos[1].index.add(["pa1.rubric.txt"])
        student_git_repos[1].index.commit("Finished grading")
        
        result = graders[0].run("grader push-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)                
        
        # The non-master instructor pulls the repos and generates a report

        result = instructors[1].run("instructor grading pull-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)        
        
        result = instructors[1].run("instructor grading show-grading-status", ["--by-grader", "pa1"])
        self.assertEquals(result.exit_code, 0)   
        
        # Grader 2 pulls their grading
                
        result = graders[1].run("grader pull-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)        
                    
        student3_grading_repo_path = "chisubmit-test/repositories/%s/%s/%s" % (course_id, "pa1", "student3")
        student4_grading_repo_path = "chisubmit-test/repositories/%s/%s/%s" % (course_id, "pa1", "student4")
            
        student_git_repos[2], student_git_paths[2] = graders[1].get_local_git_repository(student3_grading_repo_path)
        student_git_repos[3], student_git_paths[3] = graders[1].get_local_git_repository(student4_grading_repo_path)
  
        student3_rubric_path = "%s/pa1.rubric.txt" % student_git_paths[2] 
        student4_rubric_path = "%s/pa1.rubric.txt" % student_git_paths[3] 
                

        # Grader 2 adds the empty rubrics (which should be generated by pull-grading)
        
        result = graders[1].run("grader validate-rubrics", ["pa1"])
        self.assertEquals(result.exit_code, 0)        
            
        student_git_repos[2].index.add(["pa1.rubric.txt"])
        student_git_repos[2].index.commit("Added rubric")        
        student_git_repos[3].index.add(["pa1.rubric.txt"])
        student_git_repos[3].index.commit("Added rubric")        

        result = graders[1].run("grader push-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)               

        # The non-master instructor pulls the repos and generates a report

        result = instructors[1].run("instructor grading pull-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)        
        
        result = instructors[1].run("instructor grading show-grading-status", ["--by-grader", "pa1"])
        self.assertEquals(result.exit_code, 0)   
        
        
        # Grader 2 grades student3 but does only a partial grading of student4
            
        student3_rubric = """Points:
    The PA1 Tests:
        Points Possible: 50
        Points Obtained: 20

    The PA1 Design:
        Points Possible: 50
        Points Obtained: 15

Total Points: 35 / 100

Comments: >
    Needs improvement!"""
                
        with open(student3_rubric_path, "w") as f:
            f.write(student3_rubric)

        student4_rubric = """Points:
    The PA1 Tests:
        Points Possible: 50
        Points Obtained: 35

    The PA1 Design:
        Points Possible: 50
        Points Obtained: 

Total Points: 35 / 100

Comments: >
"""
                
        with open(student4_rubric_path, "w") as f:
            f.write(student4_rubric)

        result = graders[1].run("grader validate-rubrics", ["pa1"])
        self.assertEquals(result.exit_code, 0)        

        student_git_repos[2].index.add(["pa1.rubric.txt"])
        student_git_repos[2].index.commit("Finished grading")

        student_git_repos[3].index.add(["pa1.rubric.txt"])
        student_git_repos[3].index.commit("Grading in progress")

        result = graders[1].run("grader push-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)
        
        # The non-master instructor pulls the repos and generates a report

        result = instructors[1].run("instructor grading pull-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)        
        
        result = instructors[1].run("instructor grading show-grading-status", ["--by-grader", "pa1"])
        self.assertEquals(result.exit_code, 0)   
        
        # Grader 2 finishes grading
        
        student4_rubric = """Points:
    The PA1 Tests:
        Points Possible: 50
        Points Obtained: 35

    The PA1 Design:
        Points Possible: 50
        Points Obtained: 25

Total Points: 60 / 100

Comments: >
"""
                
        with open(student4_rubric_path, "w") as f:
            f.write(student4_rubric)

        result = graders[1].run("grader validate-rubrics", ["pa1"])
        self.assertEquals(result.exit_code, 0)        

        student_git_repos[3].index.add(["pa1.rubric.txt"])
        student_git_repos[3].index.commit("Finished grading")        
        
        result = graders[1].run("grader push-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)    
        
        # The non-master instructor pulls the repos and generates a report

        result = instructors[1].run("instructor grading pull-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)        
        
        result = instructors[1].run("instructor grading show-grading-status", ["--by-grader", "pa1"])
        self.assertEquals(result.exit_code, 0)   
        
                    
        # The master instructor pulls the repos and pushes them to the students

        result = instructors[0].run("instructor grading pull-grading", ["pa1"])
        self.assertEquals(result.exit_code, 0)
        
        result = instructors[0].run("instructor grading show-grading-status", ["--by-grader", "pa1"])
        self.assertEquals(result.exit_code, 0)             
        
        result = instructors[0].run("instructor grading collect-rubrics", ["pa1"])
        self.assertEquals(result.exit_code, 0)
        
        result = instructors[0].run("instructor grading show-grading-status", ["--use-stored-grades", "--by-grader", "pa1"])
        self.assertEquals(result.exit_code, 0)  
                
        result = instructors[0].run("instructor grading list-grades")
        self.assertEquals(result.exit_code, 0)
                
        result = instructors[0].run("instructor grading push-grading", ["--to-students", "--yes", "pa1"])
        self.assertEquals(result.exit_code, 0) 
    
        for student_id, student in zip(student_ids, students):
            repo, path = student.get_local_git_repository(student_id)
            repo.remote("origin").pull("pa1-grading:pa1-grading")
            repo.heads["pa1-grading"].checkout()        
            self.assertTrue(os.path.exists(path + "/pa1.rubric.txt"))
    
    
        
from rest_framework.test import APILiveServerTestCase
from chisubmit import client
    
COURSE1_INSTRUCTORS = ["instructor1"]
COURSE1_GRADERS =     ["grader1", "grader2"]
COURSE1_STUDENTS =    ["student1", "student2", "student3", "student4"]
COURSE1_USERS = COURSE1_INSTRUCTORS + COURSE1_GRADERS + COURSE1_STUDENTS
COURSE1_ASSIGNMENTS = ["pa1", "pa2"]

COURSE2_INSTRUCTORS = ["instructor2"]
COURSE2_GRADERS =     ["grader3", "grader4"]
COURSE2_STUDENTS =    ["student5", "student6", "student7", "student8"]
COURSE2_USERS = COURSE2_INSTRUCTORS + COURSE2_GRADERS + COURSE2_STUDENTS
COURSE2_ASSIGNMENTS = ["hw1", "hw2"]
    
ALL_USERS = list(set(COURSE1_USERS + COURSE2_USERS + ["admin"]))    
    
class ChisubmitClientLibsTests(APILiveServerTestCase):
        
    def get_api_client(self, api_token, deferred_save = False):
        base_url = self.live_server_url + "/api/v1"
        
        return client.Chisubmit(api_token=api_token, base_url=base_url, deferred_save=deferred_save)  
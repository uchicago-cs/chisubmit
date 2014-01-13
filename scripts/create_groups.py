#!/usr/bin/python

import sys
import traceback

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage as CredentialStorage
from oauth2client.tools import run as run_oauth2

import gdata.spreadsheets.client

import chisubmit.core
from chisubmit.core.model import Course, Team, Student
from chisubmit.core.repos import GithubConnection
from chisubmit.core import ChisubmitException


CLIENT_SECRETS_FILE = 'client_secrets.json'
CREDENTIALS_FILE = 'credentials.json'
SCOPE = "https://spreadsheets.google.com/feeds"
SPREADSHEET_KEY = open("spreadsheet_key").read().strip()

GROUPNAME = 'groupname'
STUDENT1_CNETID = 'cnetid1'
STUDENT1_FNAME = 'firstname1'
STUDENT1_LNAME = 'lastname1'
STUDENT1_EMAIL = 'e-mail1'
STUDENT1_GITHUB = 'githubusername1'
STUDENT2_CNETID = 'cnetid2'
STUDENT2_FNAME = 'firstname2'
STUDENT2_LNAME = 'lastname2'
STUDENT2_EMAIL = 'e-mail2'
STUDENT2_GITHUB = 'githubusername2'


if len(sys.argv) != 2:
    print "Usage: create_groups.py COURSE_ID"
    exit(1)

course_id = sys.argv[1]

# Initialize chisubmit
# We assume default chisubmit directory and configuration file are used
chisubmit.core.init_chisubmit()
course = Course.from_course_id(course_id)

if course is None:
    print "Course %s does not exist"
    exit(1)

# Do the OAuth2 dance
flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=SCOPE, message="Client secrets file does not exist.")
credential_storage = CredentialStorage(CREDENTIALS_FILE)
credentials = credential_storage.get()

if credentials == None or credentials.invalid:
    credentials = run_oauth2(flow, credential_storage)

client = gdata.spreadsheets.client.SpreadsheetsClient()
token = gdata.gauth.OAuth2Token(client_id=flow.client_id, 
                                client_secret=flow.client_secret, 
                                scope=flow.scope,
                                user_agent="chisubmit", 
                                access_token=credentials.access_token, 
                                refresh_token=credentials.refresh_token)
token.authorize(client)

# Open spreadsheet
worksheets = client.get_worksheets(SPREADSHEET_KEY)

# Get first worksheet
worksheet_id = worksheets.entry[0].get_worksheet_id()

feed = client.get_list_feed(SPREADSHEET_KEY, worksheet_id)

for row in feed.entry:
    print "============================================"
    group = row.to_dict()

    if course.teams.has_key(group[GROUPNAME]):
        print "Skipping '%s'. Already exists." % group[GROUPNAME] 
        continue
    
    print "Adding group '%s'" % group[GROUPNAME]
    
    if course.students.has_key(group[STUDENT1_CNETID]):
        print "Skipping %s %s (%s). Already exists." % (group[STUDENT1_FNAME], group[STUDENT1_LNAME], group[STUDENT1_CNETID])
        student1 = course.students[group[STUDENT1_CNETID]];
    else:    
        student1 = Student(student_id = group[STUDENT1_CNETID],
                          first_name = group[STUDENT1_FNAME],
                          last_name  = group[STUDENT1_LNAME],
                          email      = group[STUDENT1_EMAIL],
                          github_id  = group[STUDENT1_GITHUB])
        course.add_student(student1)
        print "Added student %s %s (%s)." % (student1.first_name, student1.last_name, student1.id)

    if course.students.has_key(group[STUDENT2_CNETID]):
        print "Skipping %s %s (%s). Already exists." % (group[STUDENT2_FNAME], group[STUDENT2_LNAME], group[STUDENT2_CNETID])
        student2 = course.students[group[STUDENT2_CNETID]];
    else:    
        student2 = Student(student_id = group[STUDENT2_CNETID],
                          first_name = group[STUDENT2_FNAME],
                          last_name  = group[STUDENT2_LNAME],
                          email      = group[STUDENT2_EMAIL],
                          github_id  = group[STUDENT2_GITHUB])
        course.add_student(student2)
        print "Added student %s %s (%s)." % (student2.first_name, student2.last_name, student2.id)
    
    team = Team(team_id = group[GROUPNAME])
    course.add_team(team)
    team.add_student(student1)     
    team.add_student(student2)     
    print "Added team '%s'" % (team.id)
    
    course.save()
    
    print "Creating GitHub repository...",
    try:
        github_access_token = chisubmit.core.get_github_token()
        gh = GithubConnection(github_access_token, course.github_organization)
        gh.create_team_repository(course, team, True)
    except ChisubmitException, ce:
        print "ERROR: %s" % ce.message
        ce.print_exception()
        continue
    except Exception, e:
        print "ERROR: Unexpected exception"
        print traceback.format_exc()
        continue    
    print "done"

    course.save()

print "============================================"



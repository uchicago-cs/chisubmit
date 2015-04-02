#!/usr/bin/python

import sys
import random
import string
import requests
import click
import csv
from pprint import pprint as pp

def print_http_response(response):
    print "HTTP Status Code: %i" % response.status_code
    print
    print "HTTP Response"
    print "-------------"
    pp(response.headers.items())
    print
    pp(response.text)


@click.command(name="create-gitlab-users")
@click.argument('gitlab_hostname', type=str)
@click.argument('gitlab_token', type=str)
@click.argument('extern_uid_template', type=str)
@click.argument('csv_file', type=click.File('rb'))
@click.argument('csv_userid_column', type=str)
@click.argument('csv_fname_column', type=str)
@click.argument('csv_lname_column', type=str)
@click.argument('csv_email_column', type=str)
@click.option('--dry-run', is_flag=True)
@click.option('--id-from-email', is_flag=True)
def create_gitlab_users(gitlab_hostname, gitlab_token, extern_uid_template, csv_file, csv_userid_column, csv_fname_column, csv_lname_column, csv_email_column, dry_run, id_from_email):   
    headers = {"PRIVATE-TOKEN": gitlab_token}
    
    csvf = csv.DictReader(csv_file)
            
    for col in (csv_userid_column, csv_fname_column, csv_lname_column, csv_email_column):
        if col not in csvf.fieldnames:
            print "CSV file %s does not have a '%s' column" % (csv_file, col)
            ctx.exit(CHISUBMIT_FAIL)
        
    for entry in csvf:
        user_id = entry[csv_userid_column]
        if id_from_email:
            user_id = user_id.split("@")[0].strip()
        
        first_name = entry[csv_fname_column]
        last_name = entry[csv_lname_column]
        email = entry[csv_email_column]
    
        # Password doesn't actually matter since we use
        # LDAP authentication. Just in case, we set it to
        # something complicated
        passwd = ''.join([random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(25)])
    
        data = {"email": email, 
                "password": passwd,
                "username": user_id,
                "name": first_name + " " + last_name,
                "provider": "ldap",
                "extern_uid": extern_uid_template.replace("USER", user_id)}
    
        if dry_run:
            pp(data)
            print
        else:
            try:
                response = requests.post("https://%s/api/v3/users" % gitlab_hostname, 
                                         data=data,
                                         verify=False,
                                         headers=headers)
            except Exception, e:
                print "[ERROR] Unexpected exception when creating user %s" % user_id
        
            if response.status_code == 201:
                print "[OK] Created user %s" % user_id
            elif response.status_code == 404:
                print "[SKIP] User '%s' already exists" % user_id
            else:
                print "[ERROR] Unexpected error"
                print
                print_http_response(response)
                exit(1)

if __name__ == '__main__':
    create_gitlab_users()

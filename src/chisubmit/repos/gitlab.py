# Needed so we can import from the global "gitlab" package
from __future__ import absolute_import

from gitlab import Gitlab
import gitlab.exceptions

from chisubmit.repos import RemoteRepositoryConnectionBase, GitCommit, GitTag
from chisubmit.common import ChisubmitException
from dateutil.parser import parse
import random
import string

class GitLabConnection(RemoteRepositoryConnectionBase):

    def __init__(self, connection_string, staging):
        RemoteRepositoryConnectionBase.__init__(self, connection_string, staging)
        
        self.gitlab = None
        
        # Map course id's to GitLab group IDs
        self.gitlab_group_id = {}
        
        # Map student id's to GitLab user IDs
        self.gitlab_user_id = {}

        
    @staticmethod
    def get_server_type_name():
        return "GitLab"
    
    @staticmethod
    def get_connstr_mandatory_params():
        return ["gitlab_hostname"]

    @staticmethod
    def get_connstr_optional_params():
        return ["ldap_uid_template"]
    
    @staticmethod
    def supports_user_creation():
        return True    
    
    def get_credentials(self, username, password, delete_repo = False):
        try:
            g = Gitlab(self.gitlab_hostname)
            rv = g.login(username, password)
            if not rv:
                return None, False
            else:
                return g.currentuser()["private_token"], True
        except gitlab.exceptions.HttpError, he:
            if he.message == "401 Unauthorized":
                return None, False
            else:
                raise ChisubmitException("Unexpected error getting authorization token (Reason: %s)" % (he.message), he)
    
    def connect(self, credentials):
        # Credentials are a GitLab private token
        self.gitlab = Gitlab(self.gitlab_hostname, token=credentials)    
        try:
            # Test connection by grabbing current user
            user = self.gitlab.currentuser()
            
            if user.has_key("message") and user["message"] == "401 Unauthorized":
                raise ChisubmitException("Invalid GitLab credentials for server '%s'" % (self.gitlab_hostname))
            
            if not user.has_key("username"):
                raise ChisubmitException("Unexpected error connecting to GitLab server '%s'" % (self.gitlab_hostname))
                            
        except Exception as e:
            raise
            raise ChisubmitException("Unexpected error connecting to GitLab server '%s': %s" % (self.gitlab_hostname, e.message))       

    def disconnect(self, credentials):
        pass
    
    def init_course(self, course, fail_if_exists=True):
        group = self.__get_group(course)
        group_name = self.__get_group_name(course)
        if fail_if_exists and group is not None:
            raise ChisubmitException("Course '%s' already has a GitLab group" % group_name)
        
        if group is None:
            if self.staging:
                course_name = course.name + " - STAGING"
            else:
                course_name = course.name

            group_name = self.__get_group_name(course)
            new_group = self.gitlab.creategroup(course_name, group_name)
            if isinstance(new_group, gitlab.exceptions.HttpError):
                raise ChisubmitException("Could not create group '%s' (%s)" % (self.__get_group_name(course), str(new_group)), new_group)
                
    def deinit_course(self, course):
        group = self.__get_group(course)
        if group is not None:
            rv = self.gitlab.deletegroup(self.__get_group_id(course))
            
    def exists_user(self, course, course_user):
        gitlab_username = self._get_user_git_username(course, course_user)
        user = self.__get_user_by_username(gitlab_username)
        
        if user is None:
            return False
        else:
            return True


    def create_user(self, course, course_user):
        if self.ldap_uid_template is None:
            raise ChisubmitException("ldap_uid_template has not been set for this course")
        
        if "USER" not in self.ldap_uid_template:
            raise ChisubmitException("ldap_uid_template does not include USER: %s" % self.ldap_uid_template)
        
        gitlab_user_username = self._get_user_git_username(course, course_user)
        
        gitlab_user_name = "%s %s" % (course_user.user.first_name, course_user.user.last_name)

        gitlab_user_email = course_user.user.email
        
        # Password doesn't actually matter since we use
        # LDAP authentication. Just in case, we set it to
        # something complicated
        gitlab_user_password = ''.join([random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(25)])
        
        gitlab_extern_uid = self.ldap_uid_template.replace("USER", gitlab_user_username)
    
        self.gitlab.createuser(name = gitlab_user_name, 
                               username = gitlab_user_username, 
                               password = gitlab_user_password,
                               email = gitlab_user_email,
                               provider = "ldapmain",    # TODO: Make this configurable
                               confirm = False,
                               extern_uid = gitlab_extern_uid                           
                               )
        
    
    def update_instructors(self, course):
        for instructor in course.get_instructors():
            self.__add_user_to_course_group(course, self._get_user_git_username(course, instructor), "owner")

        # TODO: Remove instructors that may have been removed


    def update_graders(self, course):
        for grader in course.get_graders():
            self.__add_user_to_course_group(course, self._get_user_git_username(course, grader), "developer")

        # TODO: Remove instructors that may have been removed

    
    def create_team_repository(self, course, team, fail_if_exists=True, private=True):
        repo_name = self.__get_team_namespaced_project_name(course, team)
        team_members = team.get_team_members()

        student_names = ", ".join(["%s %s" % (tm.student.user.first_name, tm.student.user.last_name) for tm in team_members])
        repo_description = "%s: Team %s (%s)" % (course.name, team.team_id, student_names)
        
        if not self.staging:
            gitlab_students = []

            # Make sure users exist
            for tm in team_members:
                gitlab_student = self.__get_user_by_username(self._get_user_git_username(course, tm.student))
                if gitlab_student is None:
                    raise ChisubmitException("GitLab user '%s' does not exist " % (self._get_user_git_username(course, tm.student)))
                
                gitlab_students.append(gitlab_student)        

        project = self.__get_team_project(course, team)
        if project is not None and fail_if_exists:
            raise ChisubmitException("Repository %s already exists" % repo_name)
        
        if project is None:
            group = self.__get_group(course)
            
            if group is None:
                raise ChisubmitException("Group for course '%s' does not exist" % course.id)

            # Workaround: Our GitLab server doesn't like public repositories
            #if private:
            #    public = 0
            #else:
            #    public = 1
            
            gitlab_project = self.gitlab.createproject(team.team_id,
                                                       namespace_id = group["id"],
                                                       description = repo_description,
                                                       public = 0)
            
            if gitlab_project == False:
                raise ChisubmitException("Could not create repository %s" % repo_name)
            
            if not self.staging:                
                for gitlab_student in gitlab_students:
                    rc = self.gitlab.addprojectmember(gitlab_project["id"],
                                                      gitlab_student["id"], 
                                                      "developer")
                    
                    if rc == False:
                        raise ChisubmitException("Unable to add user %s to %s" % (gitlab_student["username"], repo_name))

                                                    
    
    def update_team_repository(self, course, team):
        repo_name = self.__get_team_namespaced_project_name(course, team)

        team_members = team.get_team_members()
        
        gitlab_project = self.__get_team_project(course, team)
        
        for tm in team_members:
            gitlab_student = self.__get_user_by_username(self._get_user_git_username(course, tm.student))
            if gitlab_student is None:
                raise ChisubmitException("GitLab user '%s' does not exist " % (self._get_user_git_username(course, tm.student)))
            rc = self.gitlab.addprojectmember(gitlab_project["id"],
                                              gitlab_student["id"], 
                                              "developer")        
            if rc == False:
                raise ChisubmitException("Unable to add user %s to %s" % (gitlab_student["username"], repo_name))
    
    
    def exists_team_repository(self, course, team):
        repo = self.__get_team_project(course, team)
        if repo is None:
            return False
        else:
            return True
    
    def get_repository_git_url(self, course, team):
        repo_name = self.__get_team_namespaced_project_name(course, team)
        hostname = self.gitlab_hostname.replace("http://","").replace("https://","")
        return "git@%s:%s.git" % (hostname, repo_name)
            
    def get_repository_http_url(self, course, team):
        repo_name = self.__get_team_namespaced_project_name(course, team)
        hostname = self.gitlab_hostname.replace("http://","").replace("https://","")
        return "https://%s/%s" % (hostname, repo_name)
    
    def get_commit(self, course, team, commit_sha):
        project_api_id = self.__get_team_project_api_id(course, team)
        gitlab_commit = self.gitlab.getrepositorycommit(project_api_id, commit_sha)
        if gitlab_commit == False:
            return None
        else:
            committer_name = gitlab_commit.get("committer_name", gitlab_commit["author_name"])
            committer_email = gitlab_commit.get("committer_email", gitlab_commit["author_email"])
            
            commit = GitCommit(gitlab_commit["id"], gitlab_commit["title"], 
                 gitlab_commit["author_name"], gitlab_commit["author_email"], parse(gitlab_commit["authored_date"]),
                 committer_name, committer_email, parse(gitlab_commit["committed_date"]))
            return commit
    
    def create_submission_tag(self, course, team, tag_name, tag_message, commit_sha):
        pass 
        # TODO: Commenting out for now, since GitLab doesn't support updating/removing
        #       tags through the API
        #        
        # project_name = self.__get_team_namespaced_project_name(course, team)
        # 
        # commit = self.get_commit(course, team, commit_sha)
        # 
        # if commit is None:
        #     raise ChisubmitException("Cannot create tag %s for commit %s (commit does not exist)" % (tag_name, commit_sha))
        # 
        # rc = self.gitlab.createrepositorytag(project_name, tag_name, commit_sha, tag_message)
        # if rc == False:
        #     raise ChisubmitException("Cannot create tag %s in project %s (error when creating tag)" % (tag_name, project_name))
    
    def update_submission_tag(self, course, team, tag_name, tag_message, commit_sha):
        # TODO: Not currently possible with current GitLab API
        pass
    
    def get_submission_tag(self, course, team, tag_name):
        project_name = self.__get_team_namespaced_project_name(course, team)
        gitlab_tag = self.__get_tag(project_name, tag_name)
        
        if gitlab_tag is None:
            return None
        
        tag = GitTag(name = gitlab_tag["name"],
             commit = self.get_commit(course, team, gitlab_tag["commit"]["id"]))
        
        return tag
    
    def delete_team_repository(self, course, team, fail_if_not_exists):
        project_name = self.__get_team_namespaced_project_name(course, team)
        project_api_id = self.__get_team_project_api_id(course, team)
        
        repo = self.__get_team_project(course, team)
        
        if repo is None:
            if fail_if_not_exists:
                raise ChisubmitException("Trying to delete a repository that doesn't exist (%s)" % (project_name))
            else:
                return 
        
        self.gitlab.deleteproject(project_api_id)
    
    def __get_group_name(self, course):
        if self.staging:
            return course.course_id + "-staging"
        else:
            return course.course_id    
    
    def __get_group_id(self, course):
        group_name = self.__get_group_name(course)
        if self.gitlab_group_id.has_key(group_name):
            return self.gitlab_group_id[group_name]
        else:
            # TODO: Paginations
            groups = self.gitlab.getgroups()
            
            if groups == False:
                raise ChisubmitException("Unable to fetch Gitlab groups %s (id: %s)" % (self.gitlab_group, self.gitlab_group_id))
    
            for group in groups:
                self.gitlab_group_id[group["path"]] = group["id"]

            if self.gitlab_group_id.has_key(group_name):
                return self.gitlab_group_id[group_name]
            else:
                return None

    def __get_user_by_username(self, username):
        # TODO: Paginations
        users = self.gitlab.getusers(search=username)
        
        if users == False:
            raise ChisubmitException("Unable to fetch Gitlab users")

        if len(users) == 0:
            return None

        for user in users:
            if user["username"] == username:
                return user

        return None

    def __get_user_id(self, user_id):
        if self.gitlab_user_id.has_key(user_id):
            return self.gitlab_user_id[user_id]
        else:
            # TODO: Paginations
            users = self.gitlab.getusers()
            
            if users == False:
                raise ChisubmitException("Unable to fetch Gitlab users")
    
            for user in users:
                self.gitlab_user_id[user_id] = user["id"]

            if self.gitlab_user_id.has_key(user_id):
                return self.gitlab_user_id[user_id]
            else:
                return None
    

    def __get_group(self, course):
        group_id = self.__get_group_id(course)
        
        if group_id == None:
            return None
        
        group = self.gitlab.getgroups(group_id = group_id)
        
        if group == False:
            return None
        else:
            return group
        
    def __get_team_namespaced_project_name(self, course, team):
        group_name = self.__get_group_name(course)
        s = "%s/%s" % (group_name, team.team_id)
        return s.lower()      
    
    def __get_team_project_api_id(self, course, team):
        project_name = self.__get_team_namespaced_project_name(course, team)
        return project_name.replace("/", "%2F")
    
    def __get_team_project(self, course, team):
        namespaced_project_name = self.__get_team_namespaced_project_name(course, team)
        project = self.gitlab.getproject(namespaced_project_name)
        
        if project == False:
            return None
        else:
            return project      
        
    def __add_user_to_course_group(self, course, username, access_level):
        group_name = self.__get_group_name(course)

        user = self.__get_user_by_username(username)
        if user is None:
            raise ChisubmitException("Couldn't add user '%s' to group '%s'. User does not exist" % (username, group_name))
        
        group_id = self.__get_group_id(course)

        if group_id is None:
            raise ChisubmitException("Couldn't add user '%s' to group '%s'. Course group does not exist" % (username, group_name))
                
        self.gitlab.addgroupmember(group_id, user["id"], access_level)
        
        # If the return code is False, we can't distinguish between
        # "failed because the user is already in the group" or
        # "failed for other reason".
        
        # TODO: Check whether user was actually added to group
    
    def __get_tag(self, project_name, tag_name):
        tags = self.gitlab.getrepositorytags(project_name)
        
        if tags == False:
            raise ChisubmitException("Couldn't get tags for project %s" % project_name)
        
        for t in tags:
            if t["id"] == tag_name:
                return t
            
        return None
            
        
    def __has_tag(self, project_name, tag_name):
        return self.__get_tag(project_name, tag_name) is not None            
    
        

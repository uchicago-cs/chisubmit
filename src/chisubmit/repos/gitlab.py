# Needed so we can import from the global "gitlab" package
from __future__ import absolute_import

from gitlab import Gitlab

from chisubmit.repos import RemoteRepositoryConnectionBase
from chisubmit.common import ChisubmitException

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
        return []
    
    @staticmethod
    def get_credentials(username, password, delete_repo = False):
        pass
    
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
            raise ChisubmitException("Unexpected error connecting to GitLab server '%s': %s" % (self.gitlab_hostname, e.message))       

    def disconnect(self, credentials):
        pass
    
    def init_course(self, course, fail_if_exists=True):
        group = self.__get_group(course)
        
        if fail_if_exists and group is not None:
            raise ChisubmitException("Course '%s' already has a GitLab group" % course.id)
        
        if group is None:
            new_group = self.gitlab.creategroup(course.name, course.id)
            
            if new_group != True:
                raise ChisubmitException("Could not create group '%s'" % course.id)
                
        for instructor in course.instructors.values():
            self.__add_user_to_course_group(course, instructor.git_server_id, "owner")

        for grader in course.graders.values():
            self.__add_user_to_course_group(course, grader.git_server_id, "developer")


    def deinit_course(self, course):
        pass
    
    def update_instructors(self, course):
        for instructor in course.instructors.values():
            self.__add_user_to_course_group(course, instructor.git_server_id, "owner")

        # TODO: Remove instructors that may have been removed


    def update_graders(self, course):
        for grader in course.graders.values():
            self.__add_user_to_course_group(course, grader.git_server_id, "developer")

        # TODO: Remove instructors that may have been removed

    
    def create_team_repository(self, course, team, fail_if_exists=True, private=True):
        repo_name = self.__get_team_namespaced_project_name(course, team)
        student_names = ", ".join(["%s %s" % (s.first_name, s.last_name) for s in team.students])
        repo_description = "%s: Team %s (%s)" % (course.name, team.id, student_names)
        
        if not self.staging:
            gitlab_students = []

            # Make sure users exist
            for s in team.students:
                gitlab_student = self.__get_user_by_username(s.git_server_id)
                
                if gitlab_student is None:
                    raise ChisubmitException("GitLab user '%s' does not exist " % (s.git_server_id))
                
                gitlab_students.append(gitlab_student)        
        
        project = self.__get_team_project(course, team)
        
        if project is not None and fail_if_exists:
            raise ChisubmitException("Repository %s already exists" % repo_name)
        
        if project is None:
            group = self.__get_group(course)
            
            if group is None:
                raise ChisubmitException("Group for course '%s' does not exist" % course.id)

            if private:
                public = 0
            else:
                public = 1
            
            gitlab_project = self.gitlab.createproject(team.id,
                                                       namespace_id = group["id"],
                                                       description = repo_description,
                                                       public = public)
            
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
        pass
    
    def exists_team_repository(self, course, team):
        pass
    
    def get_repository_git_url(self, course, team):
        repo_name = self.__get_team_namespaced_project_name(course, team)
        return "git@%s:%s.git" % (self.gitlab_hostname, repo_name)
            
    def get_repository_http_url(self, course, team):
        repo_name = self.__get_team_namespaced_project_name(course, team)
        return "https://%s/%s" % (self.gitlab_hostname, repo_name)
    
    def get_commit(self, course, team, commit_sha):
        pass
    
    def create_submission_tag(self, course, team, tag_name, tag_message, commit_sha):
        pass
    
    def update_submission_tag(self, course, team, tag_name, tag_message, commit_sha):
        pass
    
    def get_submission_tag(self, course, team, tag_name):
        pass
    
    def delete_team_repository(self, course, team):
        pass
    
    def __get_group_id(self, course):
        if self.gitlab_group_id.has_key(course.id):
            return self.gitlab_group_id[course.id]
        else:
            # TODO: Paginations
            groups = self.gitlab.getgroups()
            
            if groups == False:
                raise ChisubmitException("Unable to fetch Gitlab groups %s (id: %s)" % (self.gitlab_group, self.gitlab_group_id))
    
            for group in groups:
                self.gitlab_group_id[group["path"]] = group["id"]

            if self.gitlab_group_id.has_key(course.id):
                return self.gitlab_group_id[course.id]
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
        
        group = self.gitlab.getgroups(id_ = group_id)
        
        if group == False:
            return None
        else:
            return group
        
    def __get_team_namespaced_project_name(self, course, team):
        return "%s/%s" % (course.id, team.id)      
    
    
    def __get_team_project(self, course, team):
        project_name = self.__get_team_namespaced_project_name(course, team)
        
        project_name = project_name.replace("/", "%2F")
        
        project = self.gitlab.getproject(project_name)
        
        if project == False:
            return None
        else:
            return project      
        
    def __add_user_to_course_group(self, course, username, access_level):
        user = self.__get_user_by_username(username)
        
        if user is None:
            raise ChisubmitException("Couldn't add user '%s' to group '%s'. User does not exist" % (username, course.id))
        
        group_id = self.__get_group_id(course)

        if group_id is None:
            raise ChisubmitException("Couldn't add user '%s' to group '%s'. Course group does not exist" % (username, course.id))
                
        self.gitlab.addgroupmember(group_id, user["id"], access_level)
        
        # If the return code is False, we can't distinguish between
        # "failed because the user is already in the group" or
        # "failed for other reason".
        
        # TODO: Check whether user was actually added to group
    
        
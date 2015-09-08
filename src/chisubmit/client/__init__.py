#  Copyright (c) 2013-2014, The University of Chicago
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  - Neither the name of The University of Chicago nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.

import chisubmit.client.course
from chisubmit.client.requester import Requester

class Chisubmit(object):
    
    def __init__(self, login_or_token, base_url, password = None, deferred_save = False):
        # TODO: Validate URL 
        
        self._requester = Requester(login_or_token, password, base_url.rstrip("/"))
        self._deferred_save = deferred_save
    
    def get_courses(self):
        """
        :calls: GET /courses/
        :rtype: List of :class:`chisubmit.client.course.Course`
        """
        
        headers, data = self._requester.request(
            "GET",
            "/courses/"
        )
        return [chisubmit.client.course.Course(self, headers, elem) for elem in data]    
    
    def get_course(self, course_id):
        """
        :calls: GET /courses/:course
        :param course_id: string
        :rtype: :class:`chisubmit.client.course.Course`
        """
        assert isinstance(course_id, (str, unicode)), course_id
        
        headers, data = self._requester.request(
            "GET",
            "/courses/" + course_id
        )
        return chisubmit.client.course.Course(self, headers, data)
 
    def create_course(self, course_id, name, git_usernames = None, git_staging_usernames = None, 
                      extension_policy = None, default_extensions = None):
        """
        :calls: POST /courses/
        :param course_id: string
        :param name: string
        :param git_usernames: string
        :param git_staging_usernames: string
        :param extension_policy: string
        :param default_extensions: int
        :rtype: :class:`chisubmit.client.course.Course`
        """
        assert isinstance(course_id, (str, unicode)), course_id
        
        post_data = {"course_id": course_id,
                     "name": name}
        
        if git_usernames is not None:
            post_data["git_usernames"] = git_usernames
        if git_staging_usernames is not None:
            post_data["git_staging_usernames"] = git_staging_usernames
        if extension_policy is not None:
            post_data["extension_policy"] = extension_policy
        if default_extensions is not None:
            post_data["default_extensions"] = default_extensions
        
        headers, data = self._requester.request(
            "POST",
            "/courses/",
            data = post_data
        )
        return chisubmit.client.course.Course(self, headers, data)

    def get_users(self):
        """
        :calls: GET /users/
        :rtype: List of :class:`chisubmit.client.users.User`
        """
        
        headers, data = self._requester.request(
            "GET",
            "/users/"
        )
        return [chisubmit.client.users.User(self, headers, elem) for elem in data]    
    
    def get_user(self, username = None):
        """
        :calls: GET /users/:username or GET /user
        :param username: string
        :rtype: :class:`chisubmit.client.users.User`
        """
        assert isinstance(username, (str, unicode)) or username is None, username
        
        if username is None:
            headers, data = self._requester.request(
                "GET",
                "/user"
            )            
        else:        
            headers, data = self._requester.request(
                "GET",
                "/users/" + username
            )
        return chisubmit.client.users.User(self, headers, data)
    
    def get_user_token(self, username = None, reset=False):
        """
        :calls: GET /users/:username/token or GET /user/token
        :param username: string
        :rtype: token: string, created: bool
        """
        assert isinstance(username, (str, unicode)) or username is None, username
        
        if reset:
            params = {"reset":"true"}
        else:
            params = {}
        
        if username is None:
            headers, data = self._requester.request(
                "GET",
                "/user/token",
                params = params
            )            
        else:        
            headers, data = self._requester.request(
                "GET",
                "/users/" + username + "/token",
                params = params
            )
        
        return data["token"], data["new"]    
    
    def create_user(self, username, first_name, last_name, email):
        """
        :calls: POST /users/
        :param username: string
        :param first_name: string
        :param last_name: string
        :param email: string
        :rtype: :class:`chisubmit.client.users.User`
        """
        assert isinstance(username, (str, unicode)), username
        
        post_data = {"username": username,
                     "first_name": first_name,
                     "last_name": last_name,
                     "email": email}
        
        headers, data = self._requester.request(
            "POST",
            "/users/",
            data = post_data
        )
        return chisubmit.client.users.User(self, headers, data)    

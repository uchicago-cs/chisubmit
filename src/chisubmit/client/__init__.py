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
    
    def __init__(self, api_token, base_url, deferred_save = False):
        self._requester = Requester(api_token, base_url)
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
        return [chisubmit.client.course.Course(self._requester, headers, elem, self._deferred_save) for elem in data]    
    
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
        return chisubmit.client.course.Course(self._requester, headers, data, self._deferred_save)
    
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
        
        post_data = {"shortname": course_id,
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
        return chisubmit.client.course.Course(self._requester, headers, data, self._deferred_save)

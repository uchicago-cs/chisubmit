
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

import chisubmit.core

from chisubmit.common.utils import create_subparser
from chisubmit.core import handle_unexpected_exception
from chisubmit.core.model import Course
from chisubmit.core.repos import GithubConnection
from chisubmit.common import CHISUBMIT_SUCCESS
from chisubmit.core import ChisubmitException

def create_course_subparsers(subparsers):
    subparser = create_subparser(subparsers, "course-create", cli_do__course_create)
    subparser.add_argument('--make-default', action="store_true", dest="make_default")
    subparser.add_argument('id', type=str)
    subparser.add_argument('name', type=str)
    subparser.add_argument('extensions', type=int)

    subparser = create_subparser(subparsers, "course-install", cli_do__course_install)
    subparser.add_argument('--make-default', action="store_true", dest="make_default")
    subparser.add_argument('filename', type=str)
    
    subparser = create_subparser(subparsers, "course-github-settings", cli_do__course_github_settings)
    subparser.add_argument('organization', type=str)

    subparser = create_subparser(subparsers, "course-git-staging-settings", cli_do__course_git_staging_settings)
    subparser.add_argument('git_username', type=str)
    subparser.add_argument('git_hostname', type=str)

    subparser = create_subparser(subparsers, "course-generate-distributable", cli_do__course_generate_distributable)
    subparser.add_argument('filename', type=str)
    
    
def cli_do__course_create(course, args):
    course = Course(course_id = args.id,
                    name = args.name,
                    extensions = args.extensions)
    
    try:
        course.course_file = chisubmit.core.get_course_filename(course.id)
        course.save()
        
        if args.make_default:
            chisubmit.core.set_default_course(args.id)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS


def cli_do__course_install(course, args):
    if args.filename.startswith("http"):
        new_course = Course.from_url(args.filename)
    else:
        f = open(args.filename)
        new_course = Course.from_file(f)
        f.close()
        
    try:
        new_course.course_file = chisubmit.core.get_course_filename(new_course.id)
        new_course.save()
        
        if args.make_default:
            chisubmit.core.set_default_course(new_course.id)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS


def cli_do__course_github_settings(course, args):
    course.github_organization = args.organization
    
    try:
        # Try connecting to GitHub
        github_access_token = chisubmit.core.get_github_token()
        gh = GithubConnection(github_access_token, course.github_organization)
        
        # Create GitHub team to contain admins for this course
        course.github_admins_team = "%s-admins" % course.id
        gh.create_team(course.github_admins_team, [], "admin", fail_if_exists = False)    
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
    
    return CHISUBMIT_SUCCESS


def cli_do__course_git_staging_settings(course, args):
    course.git_staging_username = args.git_username
    course.git_staging_hostname = args.git_hostname
    
    return CHISUBMIT_SUCCESS


def cli_do__course_generate_distributable(course, args):
    course.github_admins_team = None
    course.git_staging_username = None
    course.git_staging_hostname = None
    course.students = {}
    course.teams = {}
    
    try:
        course.save(args.filename)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS
    
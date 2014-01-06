
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

import getpass

import chisubmit.core

from chisubmit.common.utils import create_subparser
from chisubmit.core.repos import GithubConnection
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.core import ChisubmitException, handle_unexpected_exception

def create_gh_subparsers(subparsers):
    subparser = create_subparser(subparsers, "gh-token-create", cli_do__gh_token_create)
    subparser.add_argument('--delete', action="store_true")
    
    
def cli_do__gh_token_create(course, args):
    
    try:
        username = raw_input("Enter your GitHub username: ")
        password = getpass.getpass("Enter your GitHub password: ")
    except KeyboardInterrupt, ki:
        exit(CHISUBMIT_FAIL)
    except Exception, e:
        handle_unexpected_exception()
    
    try:
        token = GithubConnection.get_token(username, password, delete = args.delete)
        
        if token is None:
            print "Unable to create token. Incorrect username/password."
        else:
            if args.delete:
                chisubmit.core.set_github_delete_token(token)
            else:
                chisubmit.core.set_github_token(token)
    
            print "The following token has been created: %s" % token
            print "chisubmit has been configured to use this token from now on."
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
            
    return CHISUBMIT_SUCCESS

        
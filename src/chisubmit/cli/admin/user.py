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

import click

from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.client.exceptions import UnknownObjectException
from chisubmit.cli.common import catch_chisubmit_exceptions, require_config

@click.group(name="user")
@click.pass_context
def admin_user(ctx):
    pass

@click.command(name="add")
@click.argument('username', type=str)
@click.argument('first_name', type=str)
@click.argument('last_name', type=str)
@click.argument('email', type=str)
@catch_chisubmit_exceptions
@require_config
@click.pass_context
def admin_user_add(ctx, username, first_name, last_name, email):
    try:
        user = ctx.obj["client"].get_user(username = username)
        print "ERROR: Cannot create user."
        print "       Username with user_id = %s already exists." % username
        ctx.exit(CHISUBMIT_FAIL)
    except UnknownObjectException, uoe:
        user = ctx.obj["client"].create_user(username = username,
                                             first_name = first_name,
                                             last_name = last_name,
                                             email = email)

    return CHISUBMIT_SUCCESS

@click.command(name="remove")
@click.argument('user_id', type=str)
@catch_chisubmit_exceptions
@require_config
@click.pass_context
def admin_user_remove(ctx, user_id):
    # TODO
    print "NOT IMPLEMENTED"
    
    return CHISUBMIT_SUCCESS

admin_user.add_command(admin_user_add)
admin_user.add_command(admin_user_remove)




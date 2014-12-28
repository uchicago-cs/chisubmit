
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

import os.path

import click

from chisubmit.common import CHISUBMIT_SUCCESS, ChisubmitException
from chisubmit.backend.webapp.api import ChisubmitAPIServer

def get_server(config, profile):
    p = config.get_server_profile(profile)

    if p is None:
        raise ChisubmitException("Specified server profile '%s' does not exist" % profile)
    
    server = ChisubmitAPIServer(p.get("debug", False))
    
    if p["db"] == "sqlite":
        dbfile = os.path.expanduser(p["db-sqlite-file"])
        server.connect_sqlite(dbfile)
    elif p["db"]  == "postgres":
        server.connect_postgres()
        
    return server


@click.command(name="start")
@click.option('--profile', type=str)
@click.pass_context
def server_start(ctx, profile):
    config = ctx.obj["config"]
    
    server = get_server(config, profile)

    server.start()
    
    return CHISUBMIT_SUCCESS

@click.command(name="initdb")
@click.option('--profile', type=str)
@click.option('--admin-api-key', type=str)
@click.option('--force', is_flag=True)
@click.pass_context
def server_initdb(ctx, profile, admin_api_key, force):
    config = ctx.obj["config"]
    
    server = get_server(config, profile)

    server.init_db(drop_all = force)
    admin_key = server.create_admin(admin_api_key)
    
    if admin_key is not None:
        print "Chisubmit database has been created."
        print "The administrator's API key is %s" % admin_key
    else:
        print "The Chisubmit database already exists and it contains an 'admin' user"
        print "Use --force to re-create the database from scratch."
    
    return CHISUBMIT_SUCCESS


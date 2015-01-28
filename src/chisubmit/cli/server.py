
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
import tempfile

def set_auth(server, config_profile):
    if config_profile.has_key("auth"):
        if config_profile["auth"]["type"] == "testing":
            server.set_auth_testing(config_profile["auth"]["password"])
        elif config_profile["auth"]["type"] == "ldap":
            server.set_auth_ldap(config_profile["auth"]["server-uri"],
                                 config_profile["auth"]["base-dn"])      
        else:
            raise ChisubmitException("Unrecognized authentication type: %s" % config_profile["auth"]["type"])



def get_server(config, profile):
    from chisubmit.backend.api import ChisubmitAPIServer
    
    p = config.get_server_profile(profile)

    if p is None:
        raise ChisubmitException("Specified server profile '%s' does not exist" % profile)
    
    server = ChisubmitAPIServer(p.get("debug", False))
    
    if p["db"] == "sqlite":
        dbfile = os.path.expanduser(p["db-sqlite-file"])
        server.connect_sqlite(dbfile)
    elif p["db"]  == "postgres":
        server.connect_postgres()
        
    set_auth(server, p)
                    
    return server

@click.command(name="start")
@click.option('--profile', type=str)
@click.option('--test-fixture', type=str)
@click.pass_context
def server_start(ctx, profile, test_fixture):
    config = ctx.obj["config"]
    
    if test_fixture is not None:
        from chisubmit.tests.fixtures import fixtures
        from chisubmit.tests.common import load_fixture
        from chisubmit.backend.api import ChisubmitAPIServer
        
        if not fixtures.has_key(test_fixture):
            raise ChisubmitException("Test fixture '%s' does not exist" % test_fixture)
        fixture, _ = fixtures[test_fixture]
        
        server = ChisubmitAPIServer(debug=True)
        
        if os.environ.get('WERKZEUG_RUN_MAIN') != "true":
            _ , db_filename = tempfile.mkstemp(prefix="chisubmit-test-")
            os.environ['CHISUBMIT_TEST_DB'] = db_filename
            server.connect_sqlite(db_filename)
            server.init_db()
            server.create_admin(api_key="admin")
            
            load_fixture(server.db, fixture)
            
            print "Fixture '%s' has been loaded on database %s" % (test_fixture, db_filename) 
        else:
            server.connect_sqlite(os.environ['CHISUBMIT_TEST_DB'])
            
        set_auth(server, config.get_server_profile(profile))
    else:
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


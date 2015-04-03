#!/usr/bin/python

import click
import unittest
import sys

from ConfigParser import ConfigParser

from unittest.runner import TextTestRunner

from chisubmit.tests import api
from chisubmit.tests import client
from chisubmit.tests import cli
from chisubmit.tests.integration.test_complete1 import CLICompleteWorkflowExtensionsPerTeam
from chisubmit.tests.integration.test_complete2 import CLICompleteWorkflowExtensionsPerStudent
from chisubmit.tests.integration.test_complete3 import CLICompleteWorkflowCancelSubmission

api_tests = unittest.TestLoader().loadTestsFromModule(api)
client_tests = unittest.TestLoader().loadTestsFromModule(client)
cli_tests = unittest.TestLoader().loadTestsFromModule(cli)

unit_tests = {"api": api_tests,
              "clientlibs": client_tests,
              "cli": cli_tests}

all_unittests = unittest.TestSuite(unit_tests.values())

integration_tests = {"complete1": CLICompleteWorkflowExtensionsPerTeam,
                     "complete2": CLICompleteWorkflowExtensionsPerStudent,
                     "complete3": CLICompleteWorkflowCancelSubmission}

@click.command()
@click.option("--failfast", "-f", is_flag=True)
@click.option("--quiet", "-q", is_flag=True)
@click.option("--verbose", "-v", is_flag=True)
@click.option("--buffer", "-b", is_flag=True)
@click.option("--integration-config", "-c", type=click.File())
@click.option("--integration-git-server", type=str)
@click.option("--integration-git-staging", type=str)
@click.argument('tests', type=str, default="all_unit")
def runtests(failfast, quiet, verbose, buffer, 
             integration_config, integration_git_server, integration_git_staging, 
             tests):
    verbosity = 1
    if quiet:
        verbosity = 0
    if verbose:
        verbosity = 2
        
    if integration_config is not None:
        config = ConfigParser()
        config.readfp(integration_config)
    else:
        config = None
        
    runner = TextTestRunner(verbosity=verbosity, failfast=failfast, buffer=buffer)
    
    ran = False
    
    if tests in ("all", "all_unit"):
        ran = True
        runner.run(all_unittests)
        
    if tests in unit_tests:
        ran = True
        runner.run(unit_tests[tests])
        
    if tests in integration_tests:
        ran = True
        test_class = integration_tests[tests]
        suite = unittest.TestSuite()
        for name in unittest.TestLoader().getTestCaseNames(test_class):
            test = test_class(name)
            configure_integration_test(test, config, integration_git_server, integration_git_staging)
            suite.addTest(test)
        
        runner.run(suite)
        
    if not ran:
        # TODO: Try to instantiate specific test
        try:
            suite = unittest.TestLoader().loadTestsFromName(tests)
            runner.run(suite)
        except AttributeError, ae:
            print "Unknown test: %s" % tests
    
    
def configure_integration_test(test, config, git_server, git_staging):
    if config is None and (git_server is not None or git_staging is not None):
        print "ERROR: You have specified a Git server or staging server, but have"
        print "       not provided a configuration file."
        sys.exit(1)
        
    if config is None:
        return
    
    if git_server is not None:
        if not config.has_section(git_server):
            print "ERROR: You specified a %s server, but the configuration file" % git_server
            print "       doesn't have a [%s] section" % git_server
        
        connstr = config.get(git_server, "server-connstr")
        apikey = config.get(git_server, "api-key")
        username = config.get(git_server, "username")
        
        test.set_git_server_connstr(connstr)
        test.add_api_key(git_server, apikey)
        test.set_git_server_user(username)
        
    if git_staging is not None:
        if not config.has_section(git_staging):
            print "ERROR: You specified a %s server, but the configuration file" % gitgit_staging_server
            print "       doesn't have a [%s] section" % git_staging
        
        connstr = config.get(git_staging, "staging-connstr")
        apikey = config.get(git_staging, "api-key")
        username = config.get(git_server, "username")
        
        test.set_git_staging_connstr(connstr, username)
        test.add_api_key(git_staging, apikey)
        test.set_git_staging_user(username)
            
if __name__ == "__main__":
    runtests()
    
#!/usr/bin/python

import click
import unittest
import sys
import os

from ConfigParser import ConfigParser

from django.test.runner import DiscoverRunner

import chisubmit.backend.settings

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chisubmit.backend.settings")
django.setup()

from chisubmit.tests.integration.complete.test_complete1 import CLICompleteWorkflowExtensionsPerTeam
from chisubmit.tests.integration.complete.test_complete2 import CLICompleteWorkflowExtensionsPerStudent
from chisubmit.tests.integration.complete.test_complete3 import CLICompleteWorkflowCancelSubmission


test_suites = {"api": "chisubmit.tests.unit.api",
               "clientlibs": "chisubmit.tests.integration.clientlibs",
               "cli": "chisubmit.tests.integration.cli",
         
               "complete1": CLICompleteWorkflowExtensionsPerTeam,
               "complete2": CLICompleteWorkflowExtensionsPerStudent,
               "complete3": CLICompleteWorkflowCancelSubmission}
         
unit_tests = ["api"]

integration_tests = ["clientlibs", "cli"]

complete_tests = ["complete1", "complete2", "complete3"]
 
all_except_complete = unit_tests + integration_tests

def run_complete_test(runner, name, test_config, git_server, git_staging):
    suite = unittest.TestSuite()
    test_class = test_suites[name]
    for name in unittest.TestLoader().getTestCaseNames(test_class):
        test = test_class(name)
        configure_complete_test(test, test_config, git_server, git_staging)
        suite.addTest(test)    
    runner.run_tests([], extra_tests=suite)

@click.command()
@click.option("--failfast", "-f", is_flag=True)
@click.option("--quiet", "-q", is_flag=True)
@click.option("--verbose", "-v", is_flag=True)
@click.option("--buffer", "-b", is_flag=True)
@click.option("--config", "-c", type=click.File())
@click.option("--git-server", type=str)
@click.option("--git-staging", type=str)
@click.argument('tests', type=str, default="all")
def runtests(failfast, quiet, verbose, buffer, 
             config, git_server, git_staging, 
             tests):
    verbosity = 1
    if quiet:
        verbosity = 0
    if verbose:
        from chisubmit.tests.common import set_cli_verbose
        set_cli_verbose(True)
        verbosity = 2
        
    if config is not None:
        test_config = ConfigParser()
        test_config.readfp(config)
    else:
        test_config = None

    runner = DiscoverRunner(verbosity=verbosity, failfast=failfast)
        
    ran = False
    
    if tests == "all":
        ran = True
        runner.run_tests([test_suites[t] for t in all_except_complete])
                
    if tests in all_except_complete:
        ran = True
        runner.run_tests([test_suites[tests]])
        
    if tests in complete_tests:
        ran = True
        run_complete_test(runner, tests, test_config, git_server, git_staging)
                
    if tests == "complete":
        ran = True
        for test in complete_tests:
            run_complete_test(runner, test, test_config, git_server, git_staging)
        
        
    if not ran:
        #try:
            runner.run_tests([tests])
        #except AttributeError, ae:
        #    print "Unknown test: %s" % tests
    
    
def configure_complete_test(test, config, git_server, git_staging):
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
        
        test.set_git_staging_connstr(connstr)
        test.add_api_key(git_staging, apikey)
        test.set_git_staging_user(username)
            
if __name__ == "__main__":
    runtests()
    
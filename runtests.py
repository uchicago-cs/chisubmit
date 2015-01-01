#!/usr/bin/python

import click
import unittest
from unittest.runner import TextTestRunner

from chisubmit.tests import api
from chisubmit.tests import client
from chisubmit.tests import cli
from chisubmit.tests.integration.test_complete_workflow import CLICompleteWorkflow

api_tests = unittest.TestLoader().loadTestsFromModule(api)
client_tests = unittest.TestLoader().loadTestsFromModule(client)
cli_tests = unittest.TestLoader().loadTestsFromModule(cli)

unit_tests = {"api": api_tests,
              "clientlibs": client_tests,
              "cli": cli_tests}

all_unittests = unittest.TestSuite(unit_tests.values())

integration_tests = {"complete_workflow": CLICompleteWorkflow}


@click.command()
@click.option("--failfast", "-f", is_flag=True)
@click.option("--quiet", "-q", is_flag=True)
@click.option("--verbose", "-v", is_flag=True)
@click.option("--buffer", "-b", is_flag=True)
@click.option("--integration-config", "-c", type=click.File())
@click.argument('tests', type=str, default="all_unit")
def runtests(failfast, quiet, verbose, buffer, integration_config, tests):
    verbosity = 1
    if quiet:
        verbosity = 0
    if verbose:
        verbosity = 2
        
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
            # TODO: Parameterize here
            suite.addTest(test)
        
        runner.run(suite)
        
    if not ran:
        # TODO: Try to instantiate specific test
        try:
            suite = unittest.TestLoader().loadTestsFromName(tests)
            runner.run(suite)
        except AttributeError, ae:
            print "Unknown test: %s" % tests
    
if __name__ == "__main__":
    runtests()
    
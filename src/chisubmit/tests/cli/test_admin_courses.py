from chisubmit.tests.common import ChisubmitMultiTestCase
from chisubmit.tests.fixtures import users_and_courses
import unittest

from click.testing import CliRunner        
from chisubmit.cli.admin import admin_course_list
import yaml
import os
from chisubmit.cli import chisubmit_cmd
        
class CLIAdminCourse(ChisubmitMultiTestCase, unittest.TestCase):
    
    FIXTURE = users_and_courses
        
    def test_admin_course_list(self):
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            os.mkdir(".chisubmit")
            with open('.chisubmit/chisubmit.conf', 'w') as f:
                conf = {"api-url": "NONE",
                        "api-key": "admin"}
                yaml.safe_dump(conf, f, default_flow_style=False)
    
            result = runner.invoke(chisubmit_cmd, ['--testing', 
                                                   '--dir', '.chisubmit/',
                                                   '--conf', '.chisubmit/chisubmit.conf',
                                                   'admin', 'course', 'list'])

            for course in self.FIXTURE["courses"].values():            
                self.assertIn(course["name"], result.output)
            
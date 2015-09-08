#!/usr/bin/env python
# -------------------------------------------------------------------------- #
# Copyright (c) 2013-2014, The University of Chicago
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# - Neither the name of The University of Chicago nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# -------------------------------------------------------------------------- #

from ez_setup import use_setuptools
use_setuptools(version="3.1")
from setuptools import setup, find_packages
import sys

sys.path.insert(0, './src')
from chisubmit import RELEASE


eps = ['chisubmit = chisubmit.cli:chisubmit_cmd.main']

setup(name='chisubmit',
      version=RELEASE,
      description='A system for managing assignments and teams in university courses',
      author='University of Chicago, Department of Computer Science',
      author_email='borja@cs.uchicago.edu',
      url='http://chi.cs.uchicago.edu/chisubmit/',
      package_dir = {'': 'src'},
      package_data = {'': ['src/config/*.conf']},
      packages=find_packages("src"),

      install_requires = [ "GitPython >= 1.0.1",
                           "PyGithub >= 1.25.2",
                           "click >= 5.1",
                           "colorama >= 0.3.3",
                           "docutils >= 0.12",
                           "enum34 >= 1.0.4",
                           "pyapi-gitlab >= 7.8.4",
                           "python-dateutil >= 2.4.2",
                           "pytz >= 2015.4",
                           "pyyaml >= 3.11",
                           "requests >= 2.7.0",
                           "tzlocal >= 1.2",
                         ],
      extras_require = {
                         "server" : ["django-auth-ldap >= 1.2.6",
                                     "djangorestframework >= 3.2.3", 
                                     "jsonfield >= 1.0.3",
                                     "python-ldap >= 2.4.20" 
                                     ] 
                        },
      setup_requires = [ "setuptools_git >= 1.0" ],
      include_package_data=True,

      entry_points = {
        'console_scripts': eps
        },

      zip_safe = False,

      license="Apache Software License",
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Intended Audience :: Education',
          'License :: OSI Approved :: BSD License',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2 :: Only',
          'Topic :: Education'
          ]
     )

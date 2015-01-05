#!/usr/bin/env python

import os
import readline
from pprint import pprint

from flask import *
from chisubmit.backend.webapp.api import *

os.environ['PYTHONINSPECT'] = 'True'

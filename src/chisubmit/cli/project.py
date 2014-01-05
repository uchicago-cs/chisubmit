
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

from chisubmit.common.utils import create_subparser, mkdatetime,\
    set_datetime_timezone_utc, get_datetime_now_utc, convert_timezone_to_local
from chisubmit.core.model import Project, GradeComponent

import datetime

def create_project_subparsers(subparsers):
    subparser = create_subparser(subparsers, "project-create", cli_do__project_create)
    subparser.add_argument('id', type=str)
    subparser.add_argument('name', type=str)
    subparser.add_argument('deadline', type=mkdatetime)
    
    subparser = create_subparser(subparsers, "project-grade-component-add", cli_do__project_grade_component_add)
    subparser.add_argument('project_id', type=str)
    subparser.add_argument('name', type=str)
    subparser.add_argument('points', type=int)

    subparser = create_subparser(subparsers, "project-deadline-show", cli_do__project_deadline_show)
    subparser.add_argument('project_id', type=str)
    
def cli_do__project_create(course, args):
    project = Project(project_id = args.id,
                      name = args.name,
                      deadline = args.deadline)
    course.add_project(project)
    
   
def cli_do__project_grade_component_add(course, args):
    grade_component = GradeComponent(args.name, args.points)
    course.projects[args.project_id].add_grade_component(grade_component)    
    
def cli_do__project_deadline_show(course, args):
    project = course.projects[args.project_id]
    
    now_utc = get_datetime_now_utc()
    now_local = convert_timezone_to_local(now_utc)
    
    deadline_utc = project.get_deadline()
    deadline_local = convert_timezone_to_local(deadline_utc)
        
    print project.name
    print
    print "      Now (Local): %s" % now_local.isoformat(" ")
    print " Deadline (Local): %s" % deadline_local.isoformat(" ")
    print
    print "        Now (UTC): %s" % now_utc.isoformat(" ")
    print "   Deadline (UTC): %s" % deadline_utc.isoformat(" ")
    print 
    
    extensions = project.extensions_needed(now_utc)

    if extensions == 0:
        diff = deadline_utc - now_utc
    else:
        diff = now_utc - deadline_utc  
    
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds//60)%60
    seconds = diff.seconds%60
    
    if extensions == 0:
        print "The deadline has not yet passed"
        print "You have %i days, %i hours, %i minutes, %i seconds left" % (days, hours, minutes, seconds)
    else:
        print "The deadline passed %i days, %i hours, %i minutes, %i seconds ago" % (days, hours, minutes, seconds)
        print "If you submit your project now, you will need to use %i extensions" % extensions
        
            
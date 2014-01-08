
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

from chisubmit.common.utils import create_subparser
from chisubmit.core.model import Student
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS

def create_student_subparsers(subparsers):
    subparser = create_subparser(subparsers, "student-create", cli_do__student_create)
    subparser.add_argument('id', type=str)
    subparser.add_argument('first_name', type=str)
    subparser.add_argument('last_name', type=str)
    subparser.add_argument('email', type=str)
    subparser.add_argument('github_id', type=str)
    
    subparser = create_subparser(subparsers, "student-set-dropped", cli_do__student_set_dropped)
    subparser.add_argument('id', type=str)


def cli_do__student_create(course, args):
    student = Student(student_id = args.id,
                      first_name = args.first_name,
                      last_name = args.last_name,
                      email = args.email,
                      github_id = args.github_id)
    course.add_student(student)
    
    return CHISUBMIT_SUCCESS
    
    
def cli_do__student_set_dropped(course, args):
    student = course.get_student(args.id)
    if student is None:
        print "Student %s does not exist" % args.id
        return CHISUBMIT_FAIL    
    
    student.dropped = True
    
    return CHISUBMIT_SUCCESS

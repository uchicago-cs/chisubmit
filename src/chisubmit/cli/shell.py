
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
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.core import ChisubmitException, handle_unexpected_exception

def create_shell_subparsers(subparsers):
    create_subparser(subparsers, "shell", cli_do__shell)
    
    
def cli_do__shell(course, args):
    try:
        from IPython import embed, __version__
        from IPython.config.loader import Config
        if __version__ < "1.1.0":
            print "You need IPython (>= 1.1.0) to run the chisubmit shell"
            return CHISUBMIT_FAIL
    except ImportError, ie:
        print "You need IPython (>= 1.1.0) to run the chisubmit shell"
        
    try:
        cfg = Config()
        cfg.TerminalInteractiveShell.banner1 = """
                      WELCOME TO THE CHISUBMIT SHELL
    
    Course: %s
    
    This is an IPython shell with the chisubmit data structures preloaded. 
    You can access the chisubmit objects through variable 'course'.
    
    Note: Any changes you make will NOT be saved. Use course.save() to save
    any changes you make to the chisubmit objects.
    
    """ % (course.name)
    
        prompt_config = cfg.PromptManager
        prompt_config.in_template = 'chisubmit> '
        prompt_config.in2_template = '   .\\D.> '
        prompt_config.out_template = '         > '
        embed(config = cfg)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS
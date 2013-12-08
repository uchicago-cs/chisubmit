from chisubmit.common.utils import create_subparser
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

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
        
    return CHISUBMIT_SUCCESS
import logging

def init_logging(verbose = False, debug = False):
    # debug implies verbose
    if verbose:
        level = logging.INFO
    elif debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    
    l = logging.getLogger("chisubmit")
    l.setLevel(logging.DEBUG)
    
    fh = logging.StreamHandler()
    fh.setLevel(level)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    fh.setFormatter(formatter)
    l.addHandler(fh)        

def log(msg, func):
    func(msg)

def debug(msg):
    log(msg, logging.getLogger('chisubmit').debug)

def warning(msg):
    log(msg, logging.getLogger('chisubmit').warning)
    
def info(msg):
    log(msg, logging.getLogger('chisubmit').info)

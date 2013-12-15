chisubmit
=========

chisubmit is a project submission system for university courses.

Right now, chisubmit is in its very early stages, and being developed to meet the requirements of the University of Chicago's CMSC 23300 (Networks and Distributed Systems) course. We may or may not eventually develop it into a more general-purpose tool.

There is no formal documentation yet, but the file [doc/full_example.sh](doc/full_example.sh) can give you a sense of how chisubmit works and how it is meant to be used.

To install chisubmit, clone this repository and run:

    python setup.py install --user
    
Take into account that you will need to add `~/.local/bin` to your `$PATH` to run the `chisubmit` command.

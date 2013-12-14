#!/bin/bash

set -e # Exit on first error
set -x # Print out each command

# This script presents an example of a complete chisubmit workflow, from
# creating a course and its projects, to submitting projects and grading
# them. This will eventually evolve into proper documentation for 
# chisubmit; in the interim, it can give you a good idea of what
# chisubmit does and how one interacts with it.
#
# This script is also used to test the various commands in chisubmit.
# In practice, you probably would not run all these commands individually,
# as they are designed to be easily scriptable.
#
# For simplicity, the whole script runs with a single user and a
# single github account. In reality, there would be three distinct roles:
#
#  - Administrator: Typically the instructor for the course
#  - Grader: Responsible for grading project submissions
#  - Team: A team can contain one or more students, and a team
#          can submit a project for grading.
#

 
# If you want to actually run this script, you need to edit
# file "examplerc.sample", modify the variables defined there,
# and save the file as "examplerc".
# Even if you are not going to run this script, you should
# take a look at the file to see what each variable means.
if [ -e "./examplerc" ];
then
    source examplerc
else
    echo "Cannot run the sample script."
    echo "Please create an examplerc file"
    exit 1
fi

# We start by creating a new course:

chisubmit course-create --make-default example "Example Course" 3

# The above command creates a course called "example" (with
# "Example Course" simply being a more verbose description)
# where the initial number of extensions per team is three.
# It also makes "example" the default course; this avoids
# having to specify the course in all subsequent commands.
#
# The information about the course is stored in a YAML file
# located in ~/.chisubmit/courses/example.yaml.

# Next, we provide the GitHub settings for this course:

chisubmit course-github-settings $GITHUB_ORGANIZATION

# We only need to specify the GitHub organization that will host the 
# repositories
#
# Notice how we didn't have to specify that we're working with the
# "example" course. The "chisubmit course-create" command made it
# the default course. If we wanted to specify a different course,
# we can use the "--course COURSE_NAME" option.

# Next, we create a project:

chisubmit project-create p1 "Project 1" 2042-01-14T20:00

# The project identifier is "p1", its description is "Project 1",
# and the final parameter is the deadline for the project.
# We set it artificially high, so this script doesn't fail
# because we're submitting after a deadline, etc.

# Once we've created a project, we can specify the "components"
# of that project's grade. For example, we can define that this
# project has a "Tests" component and a "Design" component,
# each worth 50 points.

chisubmit project-grade-component-add p1 Tests 50
chisubmit project-grade-component-add p1 Design 50

# Next, we create an additional project:

chisubmit project-create p2 "Project 2" 2042-01-21T20:00
chisubmit project-grade-component-add p2 Tests 50
chisubmit project-grade-component-add p2 Design 50

# Now, we add students to the course. In practice, this information
# could be collected through an online form or from an enrolment
# spreadsheet, and can easily be converted to calls to "chisubmit student-create".
#
# Notice how we use the same GitHub username just for testing
# purposes. In practice, each student needs his/her own
# GitHub account.

chisubmit student-create student1 First1 Last1 student1@uchicago.edu $GITHUB_USERNAME
chisubmit student-create student2 First2 Last2 student2@uchicago.edu $GITHUB_USERNAME
chisubmit student-create student3 First3 Last3 student3@uchicago.edu $GITHUB_USERNAME
chisubmit student-create student4 First4 Last4 student4@uchicago.edu $GITHUB_USERNAME

# Next, we create teams. Each team has two students.

chisubmit team-create team1
chisubmit team-student-add team1 student1
chisubmit team-student-add team1 student2

chisubmit team-create team2
chisubmit team-student-add team2 student3
chisubmit team-student-add team2 student4


# Once we have our teams, we create their repositories:

chisubmit team-gh-repo-create team1 --ignore-existing
chisubmit team-gh-repo-create team2 --ignore-existing


# Note: We use the --ignore-existing option here just so this script can be
# rerun without having to delete existing repositories first (which
# actually requires a personal access token with special permission)
# Ordinarily, you wouldn't have to include this option.

# Next, we assign Project 1 to each team.
#
# The reason we don't assign all the projects at once (or do this by default)
# is because team composition can (and often does) change throughout the
# quarter. So, just because the students in team1 work together on Project 1
# is no guarantee that they will be working on Project 2 too.
#
# In practice, the team-project-add command should be run once a project
# has started, and all team changes have been made.

chisubmit team-project-add team1 p1
chisubmit team-project-add team2 p1


# Now, we're going to simulate a few actions that a team would perform:
# Create a new local repository, add the GitHub repo as a remote,
# create a few files, add them to the repo, push to GitHub,
# do another commit, and push it to GitHub too.

TEAM1_REPO=`mktemp -d`
TEAM2_REPO=`mktemp -d`

TEAM1_GIT_OPTS="--git-dir=$TEAM1_REPO/.git --work-tree=$TEAM1_REPO"
TEAM2_GIT_OPTS="--git-dir=$TEAM2_REPO/.git --work-tree=$TEAM2_REPO"

git $TEAM1_GIT_OPTS init
git $TEAM2_GIT_OPTS init

git $TEAM1_GIT_OPTS remote add origin git@github.com:$GITHUB_ORGANIZATION/example-team1.git
git $TEAM2_GIT_OPTS remote add origin git@github.com:$GITHUB_ORGANIZATION/example-team2.git

touch $TEAM1_REPO/foo
touch $TEAM1_REPO/bar
touch $TEAM1_REPO/baz

touch $TEAM2_REPO/foo
touch $TEAM2_REPO/bar
touch $TEAM2_REPO/baz

git $TEAM1_GIT_OPTS add $TEAM1_REPO/
git $TEAM1_GIT_OPTS commit -m "First commit of team1"

git $TEAM2_GIT_OPTS add $TEAM2_REPO/
git $TEAM2_GIT_OPTS commit -m "First commit of team2"

# To make this script easily rerunable, we push with --force and
# delete any existing tags. You do not need to do this in practice.
git $TEAM1_GIT_OPTS push --force -u origin master
git $TEAM1_GIT_OPTS push origin :refs/tags/p1 :refs/tags/p2
git $TEAM2_GIT_OPTS push --force -u origin master
git $TEAM2_GIT_OPTS push origin :refs/tags/p1 :refs/tags/p2

echo 'Hello, world!' > $TEAM1_REPO/foo
echo 'Hello, world!' > $TEAM2_REPO/foo

git $TEAM1_GIT_OPTS add $TEAM1_REPO/
git $TEAM1_GIT_OPTS commit -m "Second commit of team1"

git $TEAM2_GIT_OPTS add $TEAM2_REPO/
git $TEAM2_GIT_OPTS commit -m "Second commit of team2"

git $TEAM1_GIT_OPTS push
git $TEAM2_GIT_OPTS push

TEAM1_SHA=`git $TEAM1_GIT_OPTS rev-parse HEAD`
TEAM2_SHA=`git $TEAM2_GIT_OPTS rev-parse HEAD`

# Finally, we submit the projects
chisubmit team-project-submit team1 p1 $TEAM1_SHA 0 --yes
chisubmit team-project-submit team2 p1 $TEAM2_SHA 0 --yes

# Now that the project has been submitted, the graders
# need to access them and grade them.
#
# The following commands would be run by a grader. They
# create a clone of the GitHub repositories in
# ~/.chisubmit/repositories/example/
# To make this script rerunnable, we first delete that
# directory
rm -rf ~/.chisubmit/repositories/example/
chisubmit team-local-repo-sync team1
chisubmit team-local-repo-sync team2

# Next, we create the grading branches:
chisubmit team-create-grading-branch team1 p1
chisubmit team-create-grading-branch team2 p1

# The above two commands will create a branch called "p1-grading"
# and will make that the current branch. Graders should only
# modify those branches, and should never mess with the master
# branch (or any other branch for that matter)

# Now, let's do some "grading"
TEAM1_GRADING_REPO="$HOME/.chisubmit/repositories/example/team1"
TEAM2_GRADING_REPO="$HOME/.chisubmit/repositories/example/team2"

TEAM1_GRADING_GIT_OPTS="--git-dir=$TEAM1_GRADING_REPO/.git --work-tree=$TEAM1_GRADING_REPO"
TEAM2_GRADING_GIT_OPTS="--git-dir=$TEAM2_GRADING_REPO/.git --work-tree=$TEAM2_GRADING_REPO"

echo 'Needs improvement' >> $TEAM1_GRADING_REPO/bar
echo 'Great job!' >> $TEAM2_GRADING_REPO/bar

git $TEAM1_GRADING_GIT_OPTS add $TEAM1_GRADING_REPO/
git $TEAM1_GRADING_GIT_OPTS commit -m "Graded p1"

git $TEAM2_GRADING_GIT_OPTS add $TEAM2_GRADING_REPO/
git $TEAM2_GRADING_GIT_OPTS commit -m "Graded p1"







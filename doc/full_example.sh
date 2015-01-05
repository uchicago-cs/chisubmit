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

chisubmit course create --make-default example "Example Course" 3


# The above command creates a course called "example" (with
# "Example Course" simply being a more verbose description)
# where the initial number of extensions per team is three.
# It also makes "example" the default course; this avoids
# having to specify the course in all subsequent commands.
#
# The information about the course is stored in a YAML file
# located in ~/.chisubmit/courses/example.yaml.

# Next, we provide the GitHub settings for this course:

chisubmit course git-server $GIT_SERVER_CONNECTIONSTRING

# And for the staging server
chisubmit course git-staging-server $GIT_STAGING_SERVER_CONNECTIONSTRING


# We only need to specify the GitHub organization that will host the 
# repositories
#
# Notice how we didn't have to specify that we're working with the
# "example" course. The "chisubmit course-create" command made it
# the default course. If we wanted to specify a different course,
# we can use the "--course COURSE_NAME" option.

# Next, we create a project:

chisubmit project create p1 "Project 1" 2042-01-14T20:00


# The project identifier is "p1", its description is "Project 1",
# and the final parameter is the deadline for the project.
# We set it artificially high, so this script doesn't fail
# because we're submitting after a deadline, etc.

# Once we've created a project, we can specify the "components"
# of that project's grade. For example, we can define that this
# project has a "Tests" component and a "Design" component,
# each worth 50 points.

chisubmit project grade-component-add p1 Tests 50
chisubmit project grade-component-add p1 Design 50

# Next, we create an additional project:

chisubmit project create p2 "Project 2" 2042-01-21T20:00
chisubmit project grade-component-add p2 Tests 50
chisubmit project grade-component-add p2 Design 50


# Add instructors to the course

chisubmit instructor create instructor1 FirstA LastA instructor1@uchicago.edu $GITHUB_USERNAME $GITHUB_USERNAME



# Now, we add students to the course. In practice, this information
# could be collected through an online form or from an enrolment
# spreadsheet, and can easily be converted to calls to "chisubmit student-create".
#
# Notice how we use the same GitHub username just for testing
# purposes. In practice, each student needs his/her own
# GitHub account.

chisubmit student create student1 First1 Last1 student1@uchicago.edu $GITHUB_USERNAME
chisubmit student create student2 First2 Last2 student2@uchicago.edu $GITHUB_USERNAME
chisubmit student create student3 First3 Last3 student3@uchicago.edu $GITHUB_USERNAME
chisubmit student create student4 First4 Last4 student4@uchicago.edu $GITHUB_USERNAME

# Next, we create teams. Each team has two students.

chisubmit team create team1
chisubmit team student-add team1 student1
chisubmit team student-add team1 student2

chisubmit team create team2
chisubmit team student-add team2 student3
chisubmit team student-add team2 student4

# Next, we create a grader
chisubmit grader create graderA FirstA LastA graderA@uchicago.edu $GITHUB_USERNAME $GITHUB_USERNAME


# Once we have our teams, we create their repositories:

chisubmit team repo-create team1 --ignore-existing --public
chisubmit team repo-create team1 --ignore-existing --public --staging

chisubmit team repo-create team2 --ignore-existing --public
chisubmit team repo-create team2 --ignore-existing --public --staging


# Note: We use the --ignore-existing option here just so this script can be
# rerun without having to delete existing repositories first (which
# actually requires a personal access token with special permission)
# Also, we create public repositories just because we usually run this
# test script on a GitHub organization without private repos.
# Ordinarily, you wouldn't have to include either of these options.

# Next, we assign Project 1 to each team.
#
# The reason we don't assign all the projects at once (or do this by default)
# is because team composition can (and often does) change throughout the
# quarter. So, just because the students in team1 work together on Project 1
# is no guarantee that they will be working on Project 2 too.
#
# In practice, the admin-assign-project command should be run once a project
# has started, and all team changes have been made.

chisubmit admin assign-project p1



# Now, we're going to simulate a few actions that a team would perform:
# Create a new local repository, add the GitHub repo as a remote,
# create a few files, add them to the repo, push to GitHub,
# do another commit, and push it to GitHub too.

if [ -e "~/.chisubmit-team1/" ];
then
    rm -rf ~/.chisubmit-team1/
fi

if [ -e "~/.chisubmit-team2/" ];
then
    rm -rf ~/.chisubmit-team2/
fi

mkdir -p ~/.chisubmit-team1/
cp ~/.chisubmit/chisubmit.conf ~/.chisubmit-team1/

mkdir -p ~/.chisubmit-team2/
cp ~/.chisubmit/chisubmit.conf ~/.chisubmit-team2/

TEAM1_OPTS="--dir ~/.chisubmit-team1/"
TEAM2_OPTS="--dir ~/.chisubmit-team2/"

chisubmit $TEAM1_OPTS course install --make-default ~/.chisubmit/courses/example.yaml
chisubmit $TEAM2_OPTS course install --make-default ~/.chisubmit/courses/example.yaml

chisubmit $TEAM1_OPTS team repo-check team1
chisubmit $TEAM2_OPTS team repo-check team2

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
git $TEAM1_GIT_OPTS push origin :refs/tags/p1 :refs/tags/p2 :refs/heads/p1-grading
git $TEAM2_GIT_OPTS push --force -u origin master
git $TEAM2_GIT_OPTS push origin :refs/tags/p1 :refs/tags/p2 :refs/heads/p1-grading

echo 'Hello, team1!' > $TEAM1_REPO/foo
echo 'Hello, team2!' > $TEAM2_REPO/foo

git $TEAM1_GIT_OPTS add $TEAM1_REPO/
git $TEAM1_GIT_OPTS commit -m "Second commit of team1"

git $TEAM2_GIT_OPTS add $TEAM2_REPO/
git $TEAM2_GIT_OPTS commit -m "Second commit of team2"

git $TEAM1_GIT_OPTS push
git $TEAM2_GIT_OPTS push

TEAM1_SHA=`git $TEAM1_GIT_OPTS rev-parse HEAD`
TEAM2_SHA=`git $TEAM2_GIT_OPTS rev-parse HEAD`

# Finally, we submit the projects
chisubmit $TEAM1_OPTS submit team1 p1 $TEAM1_SHA 0 --yes
chisubmit $TEAM2_OPTS submit team2 p1 $TEAM2_SHA 0 --yes

# Now that the project has been submitted, the admin
# needs to set up the repositories for grading.

# First of all, we can check what projects have been submitted:

chisubmit admin list-submissions p1

# Next, we get a local copy of the team repos. We refer to these
# as "grading repos". These grading repos are placed in:
#
# ~/.chisubmit/repositories/example/p1/
#
# To make this script rerunnable, we first delete that
# directory
rm -rf ~/.chisubmit/repositories/example/p1/

chisubmit admin create-grading-repos p1

# To make this script rerunable, we we push these repos to
# the staging server with --force and delete any existing tags. 
# You do not need to do this in practice (this is just so this 
# script will be rerunable).
ADMIN_TEAM1_GRADING_REPO="$HOME/.chisubmit/repositories/example/p1/team1"
ADMIN_TEAM2_GRADING_REPO="$HOME/.chisubmit/repositories/example/p1/team2"

ADMIN_TEAM1_GRADING_GIT_OPTS="--git-dir=$ADMIN_TEAM1_GRADING_REPO/.git --work-tree=$ADMIN_TEAM1_GRADING_REPO"
ADMIN_TEAM2_GRADING_GIT_OPTS="--git-dir=$ADMIN_TEAM2_GRADING_REPO/.git --work-tree=$ADMIN_TEAM2_GRADING_REPO"

git $ADMIN_TEAM1_GRADING_GIT_OPTS push --force -u staging master
git $ADMIN_TEAM1_GRADING_GIT_OPTS push staging :refs/tags/p1 :refs/tags/p2 :refs/heads/p1-grading
git $ADMIN_TEAM2_GRADING_GIT_OPTS push --force -u staging master
git $ADMIN_TEAM2_GRADING_GIT_OPTS push staging :refs/tags/p1 :refs/tags/p2 :refs/heads/p1-grading

# We create grading branches. This will result in each repo having
# a "p1-grading" branch starting from the commit tagged as "p1"
# This is the branch on which the graders will work (they should 
# never mess with the master branch (or any other branch for that matter)

chisubmit admin create-grading-branches p1

# Once we've created the grading branches, we will generate the 
# rubrics that the graders will use to specify the grades for
# each team. Some of these grades are already known by the admin
# (e.g., in the case of automated tests run on the submissions)
# So, we set those scores for the teams.

chisubmit team project-set-grade team1 p1 Tests 45
chisubmit team project-set-grade team2 p1 Tests 50

chisubmit admin add-rubrics p1

git $ADMIN_TEAM1_GRADING_GIT_OPTS add $ADMIN_TEAM1_GRADING_REPO/
git $ADMIN_TEAM1_GRADING_GIT_OPTS commit -m "Added grading rubric"

git $ADMIN_TEAM2_GRADING_GIT_OPTS add $ADMIN_TEAM2_GRADING_REPO/
git $ADMIN_TEAM2_GRADING_GIT_OPTS commit -m "Added grading rubric"

# Now, we assign graders (in this case there's only one grader,
# so she should be assigned to both teams)

chisubmit admin assign-graders p1

# And we list those assignments:

chisubmit admin list-grader-assignments p1

# Finally, we push the grading repos (with the grading branches)
# to the staging server. 
chisubmit admin push-grading-branches --staging p1


# The following commands would be run by a grader.
# We use a different configuration directory, to simulate
# that the commands are run by a different user.
mkdir -p ~/.chisubmit-grader/
mkdir -p ~/.chisubmit-grader/courses
cp ~/.chisubmit/default_course ~/.chisubmit-grader/
cp ~/.chisubmit/chisubmit.conf ~/.chisubmit-grader/
cp ~/.chisubmit/courses/example.yaml ~/.chisubmit-grader/courses/
GRADER_OPTS="--dir ~/.chisubmit-grader/"

GRADER_TEAM1_GRADING_REPO="$HOME/.chisubmit-grader/repositories/example/p1/team1"
GRADER_TEAM2_GRADING_REPO="$HOME/.chisubmit-grader/repositories/example/p1/team2"

GRADER_TEAM1_GRADING_GIT_OPTS="--git-dir=$GRADER_TEAM1_GRADING_REPO/.git --work-tree=$GRADER_TEAM1_GRADING_REPO"
GRADER_TEAM2_GRADING_GIT_OPTS="--git-dir=$GRADER_TEAM2_GRADING_REPO/.git --work-tree=$GRADER_TEAM2_GRADING_REPO"

# The following commands create a clone of the GitHub repositories in
#
# ~/.chisubmit-grader/repositories/example/p1/
#
# To make this script rerunnable, we first delete that
# directory
rm -rf ~/.chisubmit-grader/repositories/example/p1/

chisubmit $GRADER_OPTS grader create-grading-repos graderA p1

# Now, let's do some "grading"

# Grading for team1:

echo 'Needs improvement' >> $GRADER_TEAM1_GRADING_REPO/bar

echo "Points:
    Tests:
        Points Possible: 50
        Points Obtained: 45

    Design:
        Points Possible: 50
        Points Obtained: 30

Total Points: 75 / 100

Comments: >
    None" > $GRADER_TEAM1_GRADING_REPO/p1.rubric.txt

# We validate that the rubric is ok
chisubmit $GRADER_OPTS grader validate-rubric team1 p1

git $GRADER_TEAM1_GRADING_GIT_OPTS add $GRADER_TEAM1_GRADING_REPO/
git $GRADER_TEAM1_GRADING_GIT_OPTS commit -m "Graded p1"


echo 'Great job!' >> $GRADER_TEAM2_GRADING_REPO/bar

echo "Points:
    Tests:
        Points Possible: 50
        Points Obtained: 50

    Design:
        Points Possible: 50
        Points Obtained: 45

Total Points: 95 / 100

Comments: >
    None" > $GRADER_TEAM2_GRADING_REPO/p1.rubric.txt

# We validate that the rubric is ok
chisubmit $GRADER_OPTS grader validate-rubric team2 p1

# Commit
git $GRADER_TEAM2_GRADING_GIT_OPTS add $GRADER_TEAM2_GRADING_REPO/
git $GRADER_TEAM2_GRADING_GIT_OPTS commit -m "Graded p1"


# We push the grading branches to the staging repository
chisubmit $GRADER_OPTS grader push-grading-branch graderA p1


# Now, the instructor pulls the grading branches
chisubmit admin pull-grading-branches --staging p1

# Collects the rubrics
chisubmit admin collect-rubrics p1

# And pushes the grading branches to GitHub
chisubmit admin push-grading-branches --github p1



#!/bin/bash -x

chisubmit course-create --make-default example "Example Course" 3

chisubmit project-create p1 "Project 1" 2014-01-14T20:00
chisubmit project-grade-component-add p1 Tests 50
chisubmit project-grade-component-add p1 Design 50

chisubmit project-create p2 "Project 2" 2014-01-21T20:00
chisubmit project-grade-component-add p2 Tests 50
chisubmit project-grade-component-add p2 Design 50

chisubmit project-create p3 "Project 3" 2014-01-28T20:00
chisubmit project-grade-component-add p3 Tests 50
chisubmit project-grade-component-add p3 Design 50

chisubmit student-create student1 First1 Last1 student1@uchicago.edu github1
chisubmit student-create student2 First2 Last2 student2@uchicago.edu github2
chisubmit student-create student3 First3 Last3 student3@uchicago.edu github3
chisubmit student-create student4 First4 Last4 student4@uchicago.edu github4
chisubmit student-create student5 First5 Last5 student5@uchicago.edu github5
chisubmit student-create student6 First6 Last6 student6@uchicago.edu github6

chisubmit team-create team1
chisubmit team-student-add team1 student1
chisubmit team-student-add team1 student2

chisubmit team-create team2
chisubmit team-student-add team2 student3
chisubmit team-student-add team2 student4

chisubmit team-create team3
chisubmit team-student-add team3 student5
chisubmit team-student-add team3 student6

chisubmit team-project-add team1 p1
chisubmit team-project-add team2 p1
chisubmit team-project-add team3 p1



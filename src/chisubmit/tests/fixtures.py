from __future__ import unicode_literals

users_and_courses = \
{ "users": { "jinstr": {"first_name": "Joe",
                        "last_name": "Instructor",
                        "id": "jinstr",
                        "api_key": "jinstr"},
             
             "sinstr": {"first_name": "Sam",
                        "last_name": "Instructor",
                        "id": "sinstr",
                        "api_key": "sinstr"},
            },
 "courses": { "cmsc40100": {"id": "cmsc40100",
                            "name": "Introduction to Software Testing",
                            "instructors": ["jinstr"]},
              "cmsc40110": {"id": "cmsc40110",
                            "name": "Advanced Software Testing",
                            "instructors": ["sinstr"]}
            }
}

def gen_users(ninstructors, ngraders, nstudents):
    
    def __gen_users(prefix, n):
        u = {}
        for i in range(n):
            username = prefix + str(i+1)
            u[username] = {"first_name": "F_" + username,
                            "last_name": "L_" + username,
                            "id": username,
                            "api_key": username}
        return u
    
    users = {}
    
    users.update(__gen_users("instructor", ninstructors))
    users.update(__gen_users("grader", ngraders))
    users.update(__gen_users("student", nstudents))
    
    return users

complete_course = \
{ "users": gen_users(ninstructors = 1, ngraders = 2, nstudents = 4),
 "courses": { "cmsc40100": {"id": "cmsc40100",
                            "name": "Introduction to Software Testing",
                            "instructors": ["instructor1"],
                            "graders": ["grader1", "grader2"],
                            "students": ["student1", "student2", "student3", "student4"],
                            "assignments": { "pa1": {"id": "pa1",
                                                     "name": "Programming Assignment 1",
                                                     "deadline": "2042-01-21T20:00+00:00"},
                                             "pa2": {"id": "pa2",
                                                     "name": "Programming Assignment 2",
                                                     "deadline": "2042-01-28T20:00+00:00"}
                                            }
                            }
            }
}

fixtures = { "users_and_courses": (users_and_courses, 
                                   """Fixture with two users and two courses.
                                   Each course has one of the users as the sole instructor."""),
             "complete_course": (complete_course,
                                 """Fixture with a single course with 1 instructor, 2 graders,
                                 4 students, 2 assignments, but no teams. Represents a course
                                 at the start of the term.""")            
            }
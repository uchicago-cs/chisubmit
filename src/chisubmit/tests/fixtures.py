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

fixtures = { "users_and_courses": (users_and_courses, 
                                   """Fixture with two users and two courses.
                                   Each course has one of the users as the sole instructor.""")}
from api.students.models import Student
from api import manager

manager.create_api(Student, methods=['GET', 'PUT', 'POST', 'DELETE'],
                   include_columns=['student_id',
                                    'first_name',
                                    'last_name',
                                    'email',
                                    'github_id'])

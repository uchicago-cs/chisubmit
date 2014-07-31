from api.instructors.models import Instructor
from api import manager

manager.create_api(Instructor, methods=['GET', 'PUT', 'POST', 'DELETE'],
                   include_columns=['instructor_id',
                                    'first_name',
                                    'last_name',
                                    'email'])

from api import manager
from api.courses.models import Course

manager.create_api(Course, methods=['GET', 'PUT', 'PATCH', 'POST', 'DELETE'],
                   primary_key='course_id')

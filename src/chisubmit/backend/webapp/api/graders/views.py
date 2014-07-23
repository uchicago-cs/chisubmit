from api.graders.models import Grader
from api import manager

manager.create_api(Grader, methods=['GET', 'PUT', 'POST', 'DELETE'],
                   primary_key='grader_id')

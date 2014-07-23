from api.projects.models import Project
from api import manager

manager.create_api(Project, methods=['GET', 'PUT', 'POST', 'DELETE'],
                   primary_key='project_id')

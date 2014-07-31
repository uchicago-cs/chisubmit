from api.teams.models import Team
from api import manager

manager.create_api(Team, methods=['GET', 'PUT', 'PATCH', 'POST', 'DELETE'],
                   primary_key='team_id',
                   include_columns=['team_id', '.git_repo_created',
                                    'active', '.git_staging_repo_created',
                                    'course_id', 'private_name',
                                    'students', 'projects'])

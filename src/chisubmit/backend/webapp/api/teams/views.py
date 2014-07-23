from api.teams.models import Team
from api import manager

manager.create_api(Team, methods=['GET', 'PUT', 'PATCH', 'POST', 'DELETE'],
                   primary_key='team_id',
                   include_columns=['team_id', 'github_repo',
                                    'active', 'github_email_sent',
                                    'course_id', 'private_name',
                                    'students', 'projects'])

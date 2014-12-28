from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.teams.models import Team, StudentsTeams, ProjectsTeams
from chisubmit.backend.webapp.api.grades.models import Grade
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from flask import jsonify, request, abort
from chisubmit.backend.webapp.api.teams.forms import UpdateTeamInput,\
    CreateTeamInput, UpdateProjectTeamInput
from chisubmit.backend.webapp.auth.token import require_apikey
from chisubmit.backend.webapp.auth.authz import check_course_access_or_abort
from flask import g

@api_endpoint.route('/courses/<course_id>/teams', methods=['GET', 'POST'])
@require_apikey
def teams(course_id):
    course = Course.query.filter_by(id=course_id).first()
    
    if course is None:
        abort(404)    
    
    if request.method == 'GET':
        # TODO: SQLAlchemy-fy this
        teams = Team.query.all()
        if g.user.is_student_in(course):
            teams = [t for t in teams if g.user in t.students]

        return jsonify(teams=[team.to_dict() for team in teams])

    check_course_access_or_abort(g.user, course, 404, roles = ["instructor"])

    input_data = request.get_json(force=True)
    if not isinstance(input_data, dict):
        return jsonify(error='Request data must be a JSON Object'), 400

    form = CreateTeamInput.from_json(input_data)
    if not form.validate():
        return jsonify(errors=form.errors), 400

    team = Team()
    form.populate_obj(team)
    db.session.add(team)
    db.session.commit()

    return jsonify({'team': team.to_dict()}), 201


@api_endpoint.route('/courses/<course_id>/teams/<team_id>', methods=['GET', 'PUT'])
@require_apikey
def team(course_id, team_id):
    course = Course.query.filter_by(id=course_id).first()
    
    if course is None:
        abort(404)
            
    team = Team.query.filter_by(id=team_id).first()
    if team is None:
        abort(404)

    check_team_access_or_abort(g.user, team, 404, roles = ["instructor"])

    if request.method == 'PUT':
        input_data = request.get_json(force=True)
        if not isinstance(input_data, dict):
            return jsonify(error='Request data must be a JSON Object'), 400
        form = UpdateTeamInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400

        team.set_columns(**form.patch_data)

        if 'students' in form:
            for child_data in form.students.add:
                new_child = StudentsTeams()
                child_data.populate_obj(type("", (), dict(
                    new_child=new_child))(), 'new_child')
                db.session.add(new_child)

        if 'projects' in form:
            for child_data in form.projects.add:
                new_child = ProjectsTeams()
                child_data.populate_obj(type("", (), dict(
                    new_child=new_child))(), 'new_child')
                db.session.add(new_child)

        if 'grades' in form:
            for child_data in form.grades.add:
                new_child = Grade()
                child_data.populate_obj(type("", (), dict(
                    new_child=new_child))(), 'new_child')
                db.session.add(new_child)

        db.session.commit()

    return jsonify({'team': team.to_dict()})


@api_endpoint.route('/courses/<course_id>/teams/<team_id>/projects/<project_id>',
                    methods=['GET', 'PUT'])
@require_apikey
def projects_teams(course_id, team_id, project_id):
    course = Course.query.filter_by(id=course_id).first()
    
    if course is None:
        abort(404)    
    
    project_team = ProjectsTeams.query.filter_by(
        team_id=team_id).filter_by(
        project_id=project_id).first()

    if not project_team:
        abort(404)

    if request.method == 'PUT':
        input_data = request.get_json(force=True)
        if not isinstance(input_data, dict):
            return jsonify(error='Request data must be a JSON Object'), 400
        form = UpdateProjectTeamInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400

        project_team.set_columns(**form.patch_data)

        if 'grades' in form:
            for child_data in form.grades.add:
                new_child = Grade()
                child_data.populate_obj(type("", (), dict(
                    new_child=new_child))(), 'new_child')
                db.session.add(new_child)

        db.session.commit()

    return jsonify({'project_team': project_team.to_dict()}), 201


@api_endpoint.route('/project_teams/<project_team_id>', methods=['GET', 'PUT'])
@require_apikey
def direct_projects_teams(project_team_id):
    project_team = ProjectsTeams.query.filter_by(
        id=project_team_id).first()

    if not project_team:
        abort(404)

    if request.method == 'PUT':
        input_data = request.get_json(force=True)
        if not isinstance(input_data, dict):
            return jsonify(error='Request data must be a JSON Object'), 400
        form = UpdateProjectTeamInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400

        project_team.set_columns(**form.patch_data)

        if 'grades' in form:
            for child_data in form.grades.add:
                new_child = Grade()
                child_data.populate_obj(type("", (), dict(
                    new_child=new_child))(), 'new_child')
                db.session.add(new_child)

        db.session.commit()

    return jsonify({'project_team': project_team.to_dict()}), 201

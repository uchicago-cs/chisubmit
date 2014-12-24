from api import db
from api.teams.models import Team, StudentsTeams, ProjectsTeams
from api.grades.models import Grade
from api.blueprints import api_endpoint
from flask import jsonify, request, abort
from api.teams.forms import UpdateTeamInput,\
    CreateTeamInput, UpdateProjectTeamInput


@api_endpoint.route('/teams', methods=['GET', 'POST'])
def teams():
    if request.method == 'GET':
        return jsonify(teams=[team.to_dict() for team in Team.query.all()])

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


@api_endpoint.route('/teams/<team_id>', methods=['GET', 'PUT'])
def team(team_id):
    team = Team.query.filter_by(id=team_id).first()
    if team is None:
        abort(404)

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


@api_endpoint.route('/teams/<team_id>/projects/<project_id>',
                    methods=['GET', 'PUT'])
def projects_teams(team_id, project_id):
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

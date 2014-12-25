from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.projects.models import Project
from chisubmit.backend.webapp.api.grades.models import GradeComponent
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from flask import jsonify, request, abort
from chisubmit.backend.webapp.api.projects.forms import UpdateProjectInput


@api_endpoint.route('/projects', methods=['GET', 'POST'])
def projects_index():
    if request.method == 'GET':
        return jsonify(projects=[project.to_dict()
                       for project in Project.query.all()])

    new_project = Project(name=request.json.get('name'),
                          id=request.json.get('id'),
                          deadline=request.json.get('deadline'))
    db.session.add(new_project)
    db.session.commit()
    return jsonify({'project': new_project.to_dict()}), 201


@api_endpoint.route('/projects/<project_id>', methods=['PUT', 'GET'])
def project(project_id):
    project = Project.query.filter_by(id=project_id).first()
    # TODO 12DEC14: check permissions *before* 404
    if project is None:
        abort(404)

    if request.method == 'PUT':
        input_data = request.get_json(force=True)
        if not isinstance(input_data, dict):
            return jsonify(error='Request data must be a JSON Object'), 400
        form = UpdateProjectInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400

        project.set_columns(**form.patch_data)

        if 'grade_components' in form:
            for gc_data in form.grade_components.add:
                new_child = GradeComponent()
                gc_data.populate_obj(
                    type("", (), dict(new_child=new_child))(), 'new_child')
                db.session.add(new_child)
        db.session.commit()

    return jsonify({'project': project.to_dict()})


@api_endpoint.route('/projects/<project_id>/'
                    'grade_components/<grade_component_id>', methods=['GET'])
def grade_component_project(project_id, grade_component_id):
        grade_component = GradeComponent.query.filter_by(
            project_id=project_id).filter_by(
                name=grade_component_id).first()

        if not grade_component:
            abort(404)

        return jsonify({'grade_component': grade_component.to_dict()}), 201

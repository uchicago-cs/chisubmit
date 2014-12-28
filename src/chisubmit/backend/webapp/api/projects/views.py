from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.projects.models import Project
from chisubmit.backend.webapp.api.grades.models import GradeComponent
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from flask import jsonify, request, abort
from chisubmit.backend.webapp.api.projects.forms import UpdateProjectInput
from chisubmit.backend.webapp.auth.token import require_apikey
from chisubmit.backend.webapp.auth.authz import check_course_access_or_abort
from chisubmit.backend.webapp.api.courses.models import Course
from flask import g


@api_endpoint.route('/courses/<course_id>/projects', methods=['GET', 'POST'])
@require_apikey
def projects(course_id):
    course = Course.query.filter_by(id=course_id).first()
    
    if course is None:
        abort(404)
        
    check_course_access_or_abort(g.user, course, 404)
    
    if request.method == 'GET':
        return jsonify(projects=[project.to_dict()
                       for project in Project.query.filter_by(course_id=course_id).all()])

    check_course_access_or_abort(g.user, course, 404, roles=["instructor"])

    new_project = Project(name=request.json.get('name'),
                          id=request.json.get('id'),
                          deadline=request.json.get('deadline'),
                          course_id = course_id)
    db.session.add(new_project)
    db.session.commit()
    return jsonify({'project': new_project.to_dict()}), 201


@api_endpoint.route('/courses/<course_id>/projects/<project_id>', methods=['PUT', 'GET'])
@require_apikey
def project(course_id, project_id):
    course = Course.query.filter_by(id=course_id).first()
    
    if course is None:
        abort(404)
        
    check_course_access_or_abort(g.user, course, 404)    
    
    project = Project.query.filter_by(id=project_id).first()
    # TODO 12DEC14: check permissions *before* 404
    if project is None:
        abort(404)

    if request.method == 'PUT':
        check_course_access_or_abort(g.user, course, 404, roles=["instructor"])
        
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


@api_endpoint.route('/courses/<course_id>/projects/<project_id>/'
                    'grade_components/<grade_component_id>', methods=['GET'])
@require_apikey
def grade_component_project(course_id, project_id, grade_component_id):
        course = Course.query.filter_by(id=course_id).first()
        
        if course is None:
            abort(404)
            
        check_course_access_or_abort(g.user, course, 404)   
        
        grade_component = GradeComponent.query.filter_by(
            project_id=project_id).filter_by(
                name=grade_component_id).first()

        if not grade_component:
            abort(404)

        return jsonify({'grade_component': grade_component.to_dict()}), 201

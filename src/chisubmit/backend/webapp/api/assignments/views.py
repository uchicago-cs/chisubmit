from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.assignments.models import Assignment
from chisubmit.backend.webapp.api.grades.models import GradeComponent
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from flask import jsonify, request, abort
from chisubmit.backend.webapp.api.assignments.forms import UpdateAssignmentInput,\
    CreateAssignmentInput, RegisterAssignmentInput
from chisubmit.backend.webapp.auth.token import require_apikey
from chisubmit.backend.webapp.auth.authz import check_course_access_or_abort
from chisubmit.backend.webapp.api.courses.models import Course
from flask import g
from chisubmit.backend.webapp.api.users.models import User
from chisubmit.backend.webapp.api.teams.models import Team, StudentsTeams,\
    AssignmentsTeams


@api_endpoint.route('/courses/<course_id>/assignments', methods=['GET', 'POST'])
@require_apikey
def assignments(course_id):
    course = Course.query.filter_by(id=course_id).first()
    
    if course is None:
        abort(404)
        
    check_course_access_or_abort(g.user, course, 404)
    
    if request.method == 'GET':
        return jsonify(assignments=[assignment.to_dict()
                       for assignment in Assignment.query.filter_by(course_id=course_id).all()])

    check_course_access_or_abort(g.user, course, 404, roles=["instructor"])

    input_data = request.get_json(force=True)
    if not isinstance(input_data, dict):
        return jsonify(error='Request data must be a JSON Object'), 400
    form = CreateAssignmentInput.from_json(input_data)
    if not form.validate():
        return jsonify(errors=form.errors), 400

    assignment = Assignment()
    form.populate_obj(assignment)
    assignment.course_id = course_id
    db.session.add(assignment)
    db.session.commit()
    
    return jsonify({'assignment': assignment.to_dict()}), 201


@api_endpoint.route('/courses/<course_id>/assignments/<assignment_id>', methods=['PUT', 'GET'])
@require_apikey
def assignment(course_id, assignment_id):
    course = Course.query.filter_by(id=course_id).first()
    
    if course is None:
        abort(404)
        
    check_course_access_or_abort(g.user, course, 404)    
    
    assignment = Assignment.query.filter_by(id=assignment_id, course_id=course_id).first()
    # TODO 12DEC14: check permissions *before* 404
    if assignment is None:
        abort(404)

    if request.method == 'PUT':
        check_course_access_or_abort(g.user, course, 404, roles=["instructor"])
        
        input_data = request.get_json(force=True)
        if not isinstance(input_data, dict):
            return jsonify(error='Request data must be a JSON Object'), 400
        form = UpdateAssignmentInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400

        assignment.set_columns(**form.patch_data)

        if 'grade_components' in form:
            for gc_data in form.grade_components.add:
                new_child = GradeComponent()
                gc_data.populate_obj(
                    type("", (), dict(new_child=new_child))(), 'new_child')
                db.session.add(new_child)
        db.session.commit()

    return jsonify({'assignment': assignment.to_dict()})


@api_endpoint.route('/courses/<course_id>/assignments/<assignment_id>/register', methods=['POST'])
@require_apikey
def assignment_register(course_id, assignment_id):
    course = Course.query.filter_by(id=course_id).first()
    
    if course is None:
        abort(404)
        
    check_course_access_or_abort(g.user, course, 404, roles=["student"])    
    
    assignment = Assignment.query.filter_by(id=assignment_id, course_id=course_id).first()
    # TODO 12DEC14: check permissions *before* 404
    if assignment is None:
        abort(404)

    if request.method == 'POST':       
        input_data = request.get_json(force=True)
        if not isinstance(input_data, dict):
            return jsonify(error='Request data must be a JSON Object'), 400
        form = RegisterAssignmentInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400

        partners = []
        for p in form.partners:
            user_id = p.data
            user = User.from_id(user_id)
            
            if user is None or not user.is_student_in(course):
                error_msg = "User '%s' is either not a valid user or not a student in course '%s'" % (user_id, course_id)
                return jsonify(errors={"partners": error_msg}), 400
            
            partners.append(user)
            
        # TODO: Check if team already exists
    
        students_in_team = [g.user.id] + [u.id for u in partners]
        students_in_team.sort()
        
        team_name = "_".join(students_in_team)

        team = Team(id = team_name, course_id=course_id)
        db.session.add(team)
        
        st = StudentsTeams(team_id = team.id, 
                           course_id = course_id, 
                           student_id = g.user.id,
                           status = StudentsTeams.STATUS_CONFIRMED)
        db.session.add(st)
        
        for p in partners:
            st = StudentsTeams(team_id = team.id, 
                               course_id = course_id, 
                               student_id = p.id,
                               status = StudentsTeams.STATUS_UNCONFIRMED)
            db.session.add(st)
            
        at = AssignmentsTeams(team_id = team.id,
                              course_id = course_id,
                              assignment_id = assignment.id)
        db.session.add(at)
        
        db.session.commit()
            
        return jsonify({'team_name': team_name})


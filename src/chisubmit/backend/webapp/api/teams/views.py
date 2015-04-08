from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.teams.models import Team, StudentsTeams, AssignmentsTeams
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from flask import jsonify, request, abort
from chisubmit.backend.webapp.api.teams.forms import UpdateTeamInput,\
    CreateTeamInput, UpdateAssignmentTeamInput
from chisubmit.backend.webapp.auth.token import require_apikey
from chisubmit.backend.webapp.auth.authz import check_course_access_or_abort,\
    check_team_access_or_abort
from flask import g
from chisubmit.backend.webapp.api.courses.models import Course
from chisubmit.backend.webapp.api.teams.models import Grade
from chisubmit.backend.webapp.api.types import update_options

@api_endpoint.route('/courses/<course_id>/teams', methods=['GET', 'POST'])
@require_apikey
def teams(course_id):
    course = Course.query.filter_by(id=course_id).first()
    
    if course is None:
        abort(404)    

    check_course_access_or_abort(g.user, course, 404)
    
    if request.method == 'GET':
        # TODO: SQLAlchemy-fy this
        teams = Team.query.filter_by(course_id=course_id).all()

        if not g.user.has_instructor_or_grader_permissions(course):
            teams = [t for t in teams if g.user in t.students]
            
        teams_dict = []
        
        for team in teams:
            extension_policy = course.options.get("extension-policy", None)
            t = team.to_dict()
            t["extensions_available"] = team.get_extensions_available(extension_policy)
            teams_dict.append(t)

        return jsonify(teams=teams_dict)

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
            
    team = Team.from_id(course_id=course_id, team_id=team_id)
    if team is None:
        abort(404)

    check_team_access_or_abort(g.user, team, 404)
    
    if request.method == 'PUT':
        check_team_access_or_abort(g.user, team, 404, roles = ["instructor"])
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

        if 'assignments' in form:
            for child_data in form.assignments.add:
                new_child = AssignmentsTeams()
                child_data.populate_obj(type("", (), dict(
                    new_child=new_child))(), 'new_child')
                db.session.add(new_child)

            for child_data in form.assignments.update:
                assignment_id = child_data["assignment_id"].data

                at = AssignmentsTeams.from_id(course_id, team_id, assignment_id)

                if at is None:
                    error_msgs = ["Team %s is not registered for assignment %s" % (team_id, assignment_id)]
                    return jsonify(errors={"grades": error_msgs}), 400

                at.set_columns(**child_data.patch_data)

        if 'grades' in form:
            for child_data in form.grades.add:
                # Does the grade already exist?
                assignment_id = child_data["assignment_id"].data
                grade_component_id = child_data["grade_component_id"].data
                
                at = AssignmentsTeams.from_id(course_id, team_id, assignment_id)
                
                if at is None:
                    error_msgs = ["Team %s is not registered for assignment %s" % (team_id, assignment_id)]
                    return jsonify(errors={"grades": error_msgs}), 400
                
                grade = at.get_grade(grade_component_id)
                
                if grade is None:
                    new_child = Grade()
                    child_data.populate_obj(type("", (), dict(
                        new_child=new_child))(), 'new_child')
                    new_child.course_id = course_id
                    new_child.team_id = team_id                    
                    db.session.add(new_child)
                else:
                    grade.points = child_data["points"].data
                    db.session.add(grade)
                    
            if len(form.grades.penalties) > 0:
                penalties = form.grades.penalties.data
                for penalty in penalties:
                    assignment_id = penalty["assignment_id"]
                    penalty_value = penalty["penalties"]

                    at = AssignmentsTeams.from_id(course_id, team_id, assignment_id)
                    
                    if at is None:
                        error_msgs = ["Team %s is not registered for assignment %s" % (team_id, assignment_id)]
                        return jsonify(errors={"grades": error_msgs}), 400
                                        
                    at.penalties = penalty_value
                    db.session.add(at)
                    
        if 'extras' in form:
            if len(form.extras) > 0:
                update_options(form.extras, team.extras)
                db.session.add(team)                    

        db.session.commit()

    
    extension_policy = course.options.get("extension-policy", None)
    t = team.to_dict()
    t["extensions_available"] = team.get_extensions_available(extension_policy)

    return jsonify({'team': t})


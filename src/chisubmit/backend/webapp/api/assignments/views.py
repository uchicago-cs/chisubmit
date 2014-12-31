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

    if not g.user.is_student_in(course):
        error_msg = "You are not a student in course '%s'" % (course_id)
        return jsonify(errors={"register": error_msg}), 400

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

        students_in_team = [g.user] + partners
        
        warnings = []
        create_team = False
        
        teams = Team.find_teams_with_students(course_id, students_in_team)
                
        if len(teams) > 0:
            # Teams that have the assignment, but are *not* a perfect match
            have_assignment = []
            students_have_assignment = set()
            perfect_match = None
            
            for t in teams:
                if len(t.students) == len(students_in_team):
                    match = True
                    for s in students_in_team:
                        if s not in t.students:
                            match = False
                            break
                        
                    if match:
                        if perfect_match is None:
                            perfect_match = t
                        else:
                            # There shouldn't be more than one perfect match
                            error_msg = "There is more than one team with the exact same students in it." \
                                        "Please notify your instructor."  
                            return jsonify(errors={"fatal": error_msg}), 500
                    else:
                        if assignment in t.assignments:
                            have_assignment.append(t)
                            students_have_assignment.update(t.students)
                else:
                    if assignment in t.assignments:
                        have_assignment.append(t)
                        students_have_assignment.update(t.students)

            if len(have_assignment) > 0:
                error_msg = "'%s' is already registered for assignment '%s' in another team"
                error_msgs = [error_msg % (s.id, assignment.id) for s in students_have_assignment]
                return jsonify(errors={"partners": error_msgs}), 400                
                    
            if perfect_match is not None:
                if assignment in perfect_match.assignments:
                    user_st = [st for st in perfect_match.students_teams if st.student == g.user]
                    if len(user_st) != 1:
                        error_msg = "You appear to be registered twice in the same team." \
                                    "Please notify your instructor."
                        return jsonify(errors={"fatal": error_msg}), 500
                    user_st = user_st[0]
                    if user_st.status == StudentsTeams.STATUS_UNCONFIRMED:
                        user_st.status = StudentsTeams.STATUS_CONFIRMED
                        db.session.add(user_st)
                    elif user_st.status == StudentsTeams.STATUS_CONFIRMED:
                        warnings.append("You are already a confirmed member of this team")                        
                else:
                    at = AssignmentsTeams(team_id = perfect_match.id,
                                          course_id = course_id,
                                          assignment_id = assignment.id)
                    db.session.add(at)
            
                team_name = perfect_match.id
            else:
                create_team = True                        
        else:
            create_team = True
            
        if create_team:
            team_name = "_".join(sorted([s.id for s in students_in_team]))
    
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


from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.assignments.models import Assignment,\
    GradeComponent
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from flask import jsonify, request, abort
from chisubmit.backend.webapp.api.assignments.forms import UpdateAssignmentInput,\
    CreateAssignmentInput, RegisterAssignmentInput, SubmitAssignmentInput,\
    CancelSubmitAssignmentInput
from chisubmit.backend.webapp.auth.token import require_apikey
from chisubmit.backend.webapp.auth.authz import check_course_access_or_abort,\
    check_team_access_or_abort
from chisubmit.backend.webapp.api.courses.models import Course, CoursesStudents
from flask import g
from chisubmit.backend.webapp.api.users.models import User
from chisubmit.backend.webapp.api.teams.models import Team, StudentsTeams,\
    AssignmentsTeams
from chisubmit.common.utils import get_datetime_now_utc,\
    compute_extensions_needed
from sqlalchemy.sql.ddl import CreateTable


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
                new_child.course_id = course_id
                new_child.assignment_id = assignment_id
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
        
        team_name = form.team_name.data
        if team_name is None or len(team_name) == 0:
            team_name = None

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
            if team_name is None:
                team_name = "-".join(sorted([s.id for s in students_in_team]))
        
            team = Team(id = team_name, course_id=course_id)
            extension_policy = course.options.get("extension-policy", None)
            if extension_policy == "per_team":
                default_extensions = course.options.get("default-extensions", 0)
                team.extensions = default_extensions
            else:
                team.extensions = 0                
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


@api_endpoint.route('/courses/<course_id>/assignments/<assignment_id>/submit', methods=['POST'])
@require_apikey
def assignment_submit(course_id, assignment_id):
    now = get_datetime_now_utc()
    
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
        form = SubmitAssignmentInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400
        
        team_id = form.team_id.data
        commit_sha = form.commit_sha.data
        extensions_requested = form.extensions.data
        dry_run = form.dry_run.data
        
        team = Team.from_id(course_id=course_id, team_id=team_id)
        if team is None:
            abort(404)

        check_team_access_or_abort(g.user, team, 404)
        
        team_assignment = AssignmentsTeams.from_id(course.id,team.id,assignment.id)
        if team_assignment is None:
            msg = "Team '%s' is not registered for assignment '%s'" % (team.id, assignment.id)
            return jsonify(errors={"team":msg}), 400
        
        if team_assignment.is_ready_for_grading():
            msg = "You cannot re-submit assignment %s." % (assignment.id)
            msg = " You made a submission before the deadline, and the deadline has passed."
            return jsonify(errors={"submit":msg}), 400
        
        response = {}

        response["dry_run"] = dry_run
        
        response["prior_submission"] = {}
        response["prior_submission"]["submitted_at"] = team_assignment.submitted_at
        response["prior_submission"]["commit_sha"] = team_assignment.commit_sha
        response["prior_submission"]["extensions_used"] = team_assignment.extensions_used
        
        response["submission"] = {}
        response["submission"]["course_id"] = course.id
        response["submission"]["assignment_id"] = assignment.id
        response["submission"]["submitted_at"] = now
        response["submission"]["deadline"] = assignment.deadline
        
        extensions_needed = compute_extensions_needed(submission_time = now, deadline = assignment.deadline)
                
        extension_policy = course.options.get("extension-policy", None)
        extensions_available = team.get_extensions_available(extension_policy)
                
        if extensions_available < 0:
            error_msg = "The number of available extensions is negative"
            return jsonify(errors={"fatal": error_msg}), 500            

        response["submission"]["extensions_requested"] = extensions_requested
        response["submission"]["extensions_needed"] = extensions_needed

        response["team"] = {}
        response["team"]["id"] = team.id
        response["team"]["extensions_available_before"] = extensions_available
        
        if extensions_available + team_assignment.extensions_used >= extensions_needed and extensions_requested == extensions_needed: 
            response["success"] = True
            
            # If the team has already used extensions for a previous submission,
            # they don't count towards the number of extensions needed
            # They are 'credited' to the available extensions
            extensions_available += team_assignment.extensions_used
            
            extensions_available -= extensions_needed
            if not dry_run:
                team_assignment.extensions_used = extensions_needed
                team_assignment.commit_sha = commit_sha
                team_assignment.submitted_at = now
                
                db.session.add(team_assignment)
                db.session.commit()
        else:
            response["success"] = False
                
        response["team"]["extensions_available"] = extensions_available
        
        return jsonify(response)
        
        
@api_endpoint.route('/courses/<course_id>/assignments/<assignment_id>/cancel', methods=['POST'])
@require_apikey
def assignment_cancel_submit(course_id, assignment_id):
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
        form = CancelSubmitAssignmentInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400
        
        team_id = form.team_id.data
        
        team = Team.from_id(course_id=course_id, team_id=team_id)
        if team is None:
            abort(404)

        check_team_access_or_abort(g.user, team, 404)
        
        team_assignment = AssignmentsTeams.from_id(course.id,team.id,assignment.id)
        if team_assignment is None:
            msg = "Team '%s' is not registered for assignment '%s'" % (team.id, assignment.id)
            return jsonify(errors={"team":msg}), 400
        
        if team_assignment.is_ready_for_grading():
            msg = "You cannot cancel this submission for assignment %s." % (assignment.id)
            msg = " You made a submission before the deadline, and the deadline has passed."
            return jsonify(errors={"submit":msg}), 400        

        team_assignment.extensions_used = 0
        team_assignment.commit_sha = None
        team_assignment.submitted_at = None

        db.session.add(team_assignment)
        db.session.commit()
        
        return jsonify(success=True)
        

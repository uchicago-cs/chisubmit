from flask import jsonify, request, abort, g
from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from chisubmit.backend.webapp.api.courses.models import Course, CoursesInstructors,\
    CoursesStudents, CoursesGraders
from chisubmit.backend.webapp.api.assignments.models import Assignment
from chisubmit.backend.webapp.api.courses.forms import UpdateCourseInput, CreateCourseInput,\
    UpdateStudentInput
from chisubmit.backend.webapp.auth.token import require_apikey
from chisubmit.backend.webapp.auth.authz import check_course_access_or_abort,\
    check_admin_access_or_abort, check_user_ids_equal_or_abort
from chisubmit.backend.webapp.api.types import update_options

@api_endpoint.route('/courses', methods=['GET', 'POST'])
@require_apikey
def courses():
    if request.method == 'GET':
        # TODO: SQLAlchemy-fy this
        courses = Course.query.all()

        if not g.user.admin:
            courses = [c.to_dict() for c in courses if g.user.is_in_course(c)]
        else:
            courses = [c.to_dict() for c in courses]
        
        return jsonify(courses = courses), 200

    check_admin_access_or_abort(g.user, 404)

    input_data = request.get_json(force=True)
    if not isinstance(input_data, dict):
        return jsonify(error='Request data must be a JSON Object'), 400

    form = CreateCourseInput.from_json(input_data)
    if not form.validate():
        return jsonify(errors=form.errors), 400

    course = Course()
    form.populate_obj(course)
    db.session.add(course)
    db.session.commit()

    return jsonify({'course': course.to_dict()}), 201


@api_endpoint.route('/courses/<course_id>', methods=['PUT', 'GET'])
@require_apikey
def course(course_id):
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        abort(404)

    check_course_access_or_abort(g.user, course, 404)

    if request.method == 'GET':
        fields = []
        
        if g.user.admin:
            fields.append("options")
        
        if g.user.admin or g.user.is_instructor_in(course) or g.user.is_grader_in(course):
            fields += ['teams', 'courses_graders', 'courses_students', 'courses_instructors']

        return jsonify({'course': course.to_dict(show=fields)})
    
    if request.method == 'PUT':
        input_data = request.get_json(force=True)

        if not isinstance(input_data, dict):
            return jsonify(error='Request data must be a JSON Object'), 400
        form = UpdateCourseInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400

        if g.user.is_instructor_in(course):
            course.set_columns(**form.patch_data)

        if 'assignments' in form:
            for assignment_data in form.assignments.add:
                check_course_access_or_abort(g.user, course, 403, roles=["instructor"])
                new_assignment = Assignment()
                # anonymous class to fool the populate_obj() call
                anonymous_class = type("", (), dict(assignment=new_assignment))()
                assignment_data.populate_obj(anonymous_class, 'assignment')
                db.session.add(new_assignment)

        if 'instructors' in form:
            for child_data in form.instructors.add:
                check_admin_access_or_abort(g.user, 403)
                new_child = CoursesInstructors()
                anonymous_class = type("", (), dict(child=new_child))()
                child_data.populate_obj(anonymous_class, 'child')
                
                git_usernames = course.options.get("git-usernames", None)

                if git_usernames == "user_id":
                    new_child.repo_info = {"git-username": new_child.instructor_id}
                
                db.session.add(new_child)
                
            for child_data in form.instructors.update:
                instructor_id = child_data["instructor_id"].data
                
                if instructor_id is None:
                    instructor_id = g.user.id
                
                if not g.user.admin:
                    check_user_ids_equal_or_abort(g.user.id, instructor_id, 403)
                
                course_instructor = CoursesInstructors.query.filter_by(
                        course_id=course_id).filter_by(
                        instructor_id=instructor_id).first()
                
                # TODO: A more descriptive 400 would be better
                if not course_instructor:
                    abort(404)
            
                if g.user.admin or g.user.is_instructor_in(course):
                    course_instructor.set_columns(**child_data.patch_data)
                    
                update_options(child_data.repo_info, course_instructor.repo_info)
                
                db.session.add(course_instructor)                

        if 'students' in form:
            for child_data in form.students.add:
                check_admin_access_or_abort(g.user, 403)
                new_child = CoursesStudents()
                anonymous_class = type("", (), dict(child=new_child))()
                child_data.populate_obj(anonymous_class, 'child')

                git_usernames = course.options.get("git-usernames", None)
                
                if git_usernames == "user_id":
                    new_child.repo_info = {"git-username": new_child.student_id}
                    
                extension_policy = course.options.get("extension-policy", None)
                if extension_policy == "per_student":
                    default_extensions = course.options.get("default-extensions", 0)
                    new_child.extensions = default_extensions
                else:
                    new_child.extensions = 0
                    
                db.session.add(new_child)
                
            for child_data in form.students.update:
                student_id = child_data["student_id"].data
                if student_id is None:
                    student_id = g.user.id                
                
                if not (g.user.admin or g.user.is_instructor_in(course)):
                    check_user_ids_equal_or_abort(g.user.id, student_id, 403)
                                    
                course_student = CoursesStudents.query.filter_by(
                        course_id=course_id).filter_by(
                        student_id=student_id).first()
                
                # TODO: A more descriptive 400 would be better
                if not course_student:
                    abort(404)

                if g.user.admin or g.user.is_instructor_in(course):
                    course_student.set_columns(**child_data.patch_data)
                update_options(child_data.repo_info, course_student.repo_info)
                
                db.session.add(course_student)
        
        if 'graders' in form:
            for child_data in form.graders.add:
                check_admin_access_or_abort(g.user, 403)
                new_child = CoursesGraders()
                anonymous_class = type("", (), dict(child=new_child))()
                child_data.populate_obj(anonymous_class, 'child')

                git_usernames = course.options.get("git-usernames", None)
                
                if git_usernames == "user_id":
                    new_child.repo_info = {"git-username": new_child.grader_id}
                
                db.session.add(new_child)

            for child_data in form.graders.update:
                grader_id = child_data["grader_id"].data

                if grader_id is None:
                    grader_id = g.user.id                
                
                if not (g.user.admin or g.user.is_instructor_in(course)):
                    check_user_ids_equal_or_abort(g.user.id, grader_id, 403)                
                
                course_grader = CoursesGraders.query.filter_by(
                        course_id=course_id).filter_by(
                        grader_id=grader_id).first()
                
                # TODO: A more descriptive 400 would be better
                if not course_grader:
                    abort(404)
            
                if g.user.admin or g.user.is_instructor_in(course):
                    course_grader.set_columns(**child_data.patch_data)
                update_options(child_data.repo_info, course_grader.repo_info)
                
                db.session.add(course_grader)
                
        if 'options' in form:
            if len(form.options.update) > 0:
                check_admin_access_or_abort(g.user, 403)                
                update_options(form.options.update, course.options)
                db.session.add(course)

        db.session.commit()

        return jsonify({'course': course.to_dict()})


@api_endpoint.route('/courses/<course_id>/students/<student_id>',
                    methods=['GET'])
@require_apikey
def course_student(course_id, student_id):
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        abort(404)

    check_course_access_or_abort(g.user, course, 404, roles=["instructor","grader"])    
    
    course_student = CoursesStudents.query.filter_by(
        course_id=course_id).filter_by(
        student_id=student_id).first()

    if not course_student:
        abort(404)

    return jsonify({'student': course_student.student.to_dict()}), 201


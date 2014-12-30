from flask import jsonify, request, abort, g
from chisubmit.backend.webapp.api import db
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from chisubmit.backend.webapp.api.courses.models import Course, CoursesInstructors,\
    CoursesStudents, CoursesGraders
from chisubmit.backend.webapp.api.projects.models import Project
from chisubmit.backend.webapp.api.courses.forms import UpdateCourseInput, CreateCourseInput
from chisubmit.backend.webapp.auth.token import require_apikey
from chisubmit.backend.webapp.auth.authz import check_course_access_or_abort,\
    check_admin_access_or_abort


@api_endpoint.route('/courses', methods=['GET', 'POST'])
@require_apikey
def courses():
    if request.method == 'GET':
        # TODO: SQLAlchemy-fy this
        courses = Course.query.all()
        if not g.user.admin:
            courses = [c for c in courses if g.user.is_in_course(c)]
        return jsonify(
            courses=[course.to_dict()
                     for course in courses])

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

    if request.method == 'PUT':
        input_data = request.get_json(force=True)

        if not isinstance(input_data, dict):
            return jsonify(error='Request data must be a JSON Object'), 400
        form = UpdateCourseInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400

        course.set_columns(**form.patch_data)

        if 'projects' in form:
            for project_data in form.projects.add:
                new_project = Project()
                # anonymous class to fool the populate_obj() call
                anonymous_class = type("", (), dict(project=new_project))()
                project_data.populate_obj(anonymous_class, 'project')
                db.session.add(new_project)

        if 'instructors' in form:
            for child_data in form.instructors.add:
                new_child = CoursesInstructors()
                anonymous_class = type("", (), dict(child=new_child))()
                child_data.populate_obj(anonymous_class, 'child')
                db.session.add(new_child)

        if 'students' in form:
            for child_data in form.students.add:
                new_child = CoursesStudents()
                anonymous_class = type("", (), dict(child=new_child))()
                child_data.populate_obj(anonymous_class, 'child')
                db.session.add(new_child)

        if 'graders' in form:
            for child_data in form.graders.add:
                new_child = CoursesGraders()
                anonymous_class = type("", (), dict(child=new_child))()
                child_data.populate_obj(anonymous_class, 'child')
                db.session.add(new_child)
                
        if len(form.options.update) > 0:
            for child_data in form.options.update:
                course.options[child_data.data["name"]] = child_data.data["value"]
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

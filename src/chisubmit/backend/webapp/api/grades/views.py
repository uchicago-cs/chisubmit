from api.blueprints import api_endpoint
from api.grades.models import Grade
from flask import jsonify, abort


@api_endpoint.route('/grades/<grade_id>', methods=['GET'])
def grade(grade_id):
    grade = Grade.query.filter_by(id=grade_id).first()
    if grade is None:
        abort(404)

    return jsonify({'grade': grade.to_dict()})

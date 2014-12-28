from chisubmit.backend.webapp.api.blueprints import api_endpoint
from chisubmit.backend.webapp.api.grades.models import Grade
from flask import jsonify, abort
from chisubmit.backend.webapp.auth.token import require_apikey


@api_endpoint.route('/grades/<grade_id>', methods=['GET'])
@require_apikey
def grade(grade_id):
    grade = Grade.query.filter_by(id=grade_id).first()
    if grade is None:
        abort(404)

    return jsonify({'grade': grade.to_dict()})

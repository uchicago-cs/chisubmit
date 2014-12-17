from flask import jsonify, request, abort
from api import db
from api.blueprints import api_endpoint
from api.people.models import Person
from api.people.forms import CreatePersonInput, UpdatePersonInput


@api_endpoint.route('/people', methods=['POST'])
@api_endpoint.route('/instructors', methods=['POST'])
@api_endpoint.route('/students', methods=['POST'])
@api_endpoint.route('/graders', methods=['POST'])
def people():
    input_data = request.get_json(force=True)
    if not isinstance(input_data, dict):
        return jsonify(error='Request data must be a JSON Object'), 400

    form = CreatePersonInput.from_json(input_data)
    if not form.validate():
        return jsonify(errors=form.errors), 400

    person = Person()
    form.populate_obj(person)
    db.session.add(person)
    db.session.commit()

    return jsonify({'person': person.to_dict()}), 201


@api_endpoint.route('/graders/<person_id>', methods=['GET'])
def grader(person_id):
    person = Person.query.filter_by(id=person_id).first()
    # TODO 11DEC14: check permissions *before* 404
    if person is None:
        abort(404)

    return jsonify({'grader': person.to_dict()})


@api_endpoint.route('/people/<person_id>', methods=['PUT', 'GET'])
def person(person_id):
    person = Person.query.filter_by(id=person_id).first()
    # TODO 11DEC14: check permissions *before* 404
    if person is None:
        abort(404)

    if request.method == 'PUT':
        input_data = request.get_json(force=True)
        if not isinstance(input_data, dict):
            return jsonify(error='Request data must be a JSON Object'), 400
        form = UpdatePersonInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400

        person.set_columns(**form.patch_data)
        db.session.commit()

    return jsonify({'person': person.to_dict()})

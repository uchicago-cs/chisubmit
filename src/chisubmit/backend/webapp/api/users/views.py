from flask import jsonify, request, abort
from chisubmit.backend.webapp.api import db, app
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from chisubmit.backend.webapp.api.users.models import User
from chisubmit.backend.webapp.api.users.forms import CreateUserInput, UpdateUserInput,\
    GenerateAccessTokenInput
from chisubmit.backend.webapp.auth import ldapclient
from chisubmit.backend.webapp.auth.token import require_apikey
from chisubmit.backend.webapp.auth.authz import require_admin_access


@api_endpoint.route('/users', methods=['POST'])
@require_apikey
@require_admin_access
def users():
    input_data = request.get_json(force=True)
    if not isinstance(input_data, dict):
        return jsonify(error='Request data must be a JSON Object'), 400

    form = CreateUserInput.from_json(input_data)
    if not form.validate():
        return jsonify(errors=form.errors), 400

    user = User()
    form.populate_obj(user)
    db.session.add(user)
    db.session.commit()

    return jsonify({'user': user.to_dict()}), 201


@api_endpoint.route('/users/<user_id>', methods=['PUT', 'GET'])
@require_apikey
@require_admin_access
def user(user_id):
    user = User.query.filter_by(id=user_id).first()
    # TODO 11DEC14: check permissions *before* 404
    if user is None:
        abort(404)

    if request.method == 'PUT':
        input_data = request.get_json(force=True)
        if not isinstance(input_data, dict):
            return jsonify(error='Request data must be a JSON Object'), 400
        form = UpdateUserInput.from_json(input_data)
        if not form.validate():
            return jsonify(errors=form.errors), 400

        user.set_columns(**form.patch_data)
        db.session.commit()

    return jsonify({'user': user.to_dict()})


@api_endpoint.route('/users/<user_id>/token', methods=['POST'])
def get_token(user_id):
    user = User.query.filter_by(id=user_id).first()
    # TODO 11DEC14: check permissions *before* 404
    if user is None:
        abort(404)

    input_data = request.get_json(force=True)
    app.logger.error('GOT json: %s' % input_data)
    if not isinstance(input_data, dict):
        return jsonify(error='Request data must be a JSON Object'), 400
    form = GenerateAccessTokenInput.from_json(input_data)
    app.logger.error('Made form: %s' % form)
    if not form.validate():
        return jsonify(errors=form.errors), 400

    if ldapclient.authenticate(user.id, form.password.data):
        if form.reset:
            pass
            # User.new_token
        else:
            pass
            # User.api_key
        return jsonify({'key': 'asdfasdf'})
    else:
        return jsonify(errors={'credentials':['Not valid'] }), 400

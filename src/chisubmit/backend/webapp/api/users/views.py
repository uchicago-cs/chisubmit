from flask import jsonify, request, abort
from chisubmit.backend.webapp.api import db, app
from chisubmit.backend.webapp.api.blueprints import api_endpoint
from chisubmit.backend.webapp.api.users.models import User
from chisubmit.backend.webapp.api.users.forms import CreateUserInput, UpdateUserInput,\
    GenerateAccessTokenInput
from chisubmit.backend.webapp.auth import ldap, require_auth
from chisubmit.backend.webapp.auth.token import require_apikey
from chisubmit.backend.webapp.auth.authz import require_admin_access
from chisubmit.common.utils import gen_api_key
from flask.globals import g


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


@api_endpoint.route('/auth', methods=['POST'])
@require_auth
def get_api_key():
    input_data = request.get_json(force=True)
    if not isinstance(input_data, dict):
        return jsonify(error='Request data must be a JSON Object'), 400
    form = GenerateAccessTokenInput.from_json(input_data)
    if not form.validate():
        return jsonify(errors=form.errors), 400
    
    exists_prior = g.user.api_key is not None 

    if form.reset.data or g.user.api_key is None:
        api_key = gen_api_key()
        g.user.api_key = api_key
        db.session.add(g.user)
        db.session.commit()
        is_new = True
    else:
        api_key = g.user.api_key
        is_new = False
        
    return jsonify({'api_key': api_key, 
                    'exists_prior': exists_prior, 
                    'is_new': is_new})

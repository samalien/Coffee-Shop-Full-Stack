import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

# ROUTES


@app.route('/drinks', methods=['GET'])
def get_drinks():
    # load data from database
    drinks = Drink.query.all()

    # if no drinks found
    if drinks:
        abort(404)

    # return data to a view
    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks]
    }), 200


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()

    # if no drinks found
    if drinks:
        abort(404)

    # return data to a view
    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in drinks]
    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(payload):
    # load the request body
    body = request.get_json()
    try:
        # load data from body
        new_title = body['title']
        new_recipe = body['recipe']

        if isinstance(new_recipe, dict):
            new_recipe = [new_recipe]

        # create and insert new drinks
        drink = Drink(title=new_title, recipe=json.dumps(new_recipe))

        drink.insert()

    except BaseException:
        abort(400)
    # return data to a view
    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, drink_id):
    # load the request body
    body = request.get_json()
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    # id is not found
    if drink is None:
        abort(404)

    try:
        # load data from body
        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)

        # if title have data
        if new_title is not None:
            drink.title = new_title

        # if recipe have data
        if new_recipe is not None:
            drink.recipe = json.dumps(new_recipe)

        # upadte the table
        drink.update()

    except BaseException:
        abort(400)

    return jsonify({
        "success": True,
        "drinks": [drink.long()]
    }), 200


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, drink_id):
    # load data from database
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    # drink is not found
    if not drink:
        abort(404)

    try:
        # delete the drink
        drink.delete()
    except BaseException:
        abort(400)

    return jsonify({
        "success": True,
        "delete": drink_id
    }), 200


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(400)
def bad_request(eroor):
    return jsonify({
        'success': False,
        'error': 400,
        'message': 'bad request'
    }), 400


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': error.error['description']
    }), error.status_code


@app.errorhandler(401)
def unauthorized_error(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': 'unauthorized'
    }), 401


@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({
        'success': False,
        'error': 403,
        'message': 'forbidden'
    }), 403


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'internal server error'
    }), 500

"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify  # type: ignore
from api.models import db, User, Product, Order, OrderItem, SubscriptionPlan, Subscription, Payment, Cart, CartItem
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from sqlalchemy import select  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash  # type: ignore
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required  # type: ignore
from api.blueprint import api
from api.api_routes.products import *
from api.api_routes.payment import *
from api.api_routes.carts import *
from api.api_routes.subscription import *
from api.api_routes.subscriptionPlans import *
# Allow CORS requests to this API
CORS(api)


@api.route('/hello', methods=['POST', 'GET'])
def handle_hello():

    response_body = {
        "message": "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    }

    return jsonify(response_body), 200

# ADMIN SEED


@api.route('/seed', methods=['GET'])
def seed_admin():
    existing_admin = User.query.filter_by(email="admin@test.com").first()

    if existing_admin:
        return jsonify({"msg": "Admin already exists"}), 200

    admin = User(
        email="admin@test.com",
        password=generate_password_hash("1234"),
        name="Admin",
        age=30,
        weight=70,
        height=175,
        objective="admin",
        role="admin",
        is_active=True
    )

    db.session.add(admin)
    db.session.commit()
    print("Admin created")
    return jsonify({"msg": "Admin created"}), 201

# SEED PLANS 
@api.route('/seed-plans',methods =['GET']) 
def seed_plans():
    if SubscriptionPlan.query.count() > 0:
        return jsonify({"msg":"Plans already exist"}),200
    plans = [
        SubscriptionPlan(name="Plan Dieta", price=9.99, description="Plan de alimentacion personalizado de 12 semanas"),
        SubscriptionPlan(name="Plan Ejercicio", price=9.99, description="Plan de entrenamiento de 12 semanas"),
        SubscriptionPlan(name="Plan Completo", price=19.99, description="Plan de dieta y ejercicio personalizado de 12 semanas"),
    ]
    db.session.add_all (plans)
    db.session.commit()
    return jsonify({"msg":"Plans created"}), 201






# LOGIN/REGISTER


@api.route('/auth', methods=['POST'])
def auth():
    try:
        body = request.get_json()

        if not body or not body.get('email') or not body.get('password'):
            return jsonify({
                "success": False,
                "data": "missing info"
            }), 400

        user = db.session.execute(
            select(User).where(User.email == body.get('email'))
        ).scalar_one_or_none()

        if body.get('type') == 'register':
            if user:
                return jsonify({'success': False, 'data': 'email taken'}), 403

            hashed = generate_password_hash(body['password'])
            new_user = User(
                email=body['email'],
                password=hashed,
                name=body['name'],
                age=body['age'],
                weight=body['weight'],
                height=body['height'],
                objective=body['objective'],
                is_active=True
            )
            db.session.add(new_user)
            db.session.commit()

            token = create_access_token(identity=str(new_user.id))

            return jsonify({
                'success': True,
                'data': new_user.serialize(),
                'token': token
            }), 201

        if body.get('type') == 'login':
            if not user:
                return jsonify({'success': False, 'data': 'email not found'}), 404

            if not check_password_hash(user.password, body['password']):
                return jsonify({'success': False, 'data': 'incorrect email or password'}), 401

            token = create_access_token(identity=str(user.id))

            return jsonify({
                'success': True,
                'data': user.serialize(),
                'token': token
            }), 200

        return jsonify({'success': False, 'data': 'invalid type'}), 400
    except Exception as e:
        print("ERROR BACKEND:", e)
        return jsonify({
            "success": False,
            "data": "internal server error"}), 500
# seed test-comands

@api.route('/seed-test-data', methods=['GET'])
def seed_test_data():
    from api.commands import insert_test_data_logic
    result = insert_test_data_logic()
    return jsonify({"success": True, "data": result}), 200

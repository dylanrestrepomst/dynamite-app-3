from flask import Flask, request, jsonify  # type: ignore
from api.models import db, User, Product, Order, OrderItem, SubscriptionPlan, Subscription, Payment, Cart, CartItem
from sqlalchemy import select  # type: ignore
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required  # type: ignore
from api.blueprint import api
import pandas as pd



@api.route("/seed-products", methods=["GET"])
def seed_products():
    try:
        from api.api_routes.seedProducts import seed_products_from_csv
        count = seed_products_from_csv(
            "src/front/datasets/bodybuilding_nutrition_products.csv"
        )
        return jsonify({"success": True, "msg": f"{count} products inserted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
# ADD A NEW PRODUCT TO THE BBDD


@api.route("/products", methods=["POST"])
@jwt_required()  # PROTECTING ROUTE STEP 1
def new_product():
    user_id = get_jwt_identity()  # PROTECTING ROUTE STEP 2
    user = db.session.get(User, user_id)  # PROTECTING ROUTE

    if user.role != "admin":  # PROTECTING ROUTE STEP 3
        return jsonify({"success": False, "msg": "forbidden"}), 403

    body = request.get_json()
    if not body['name'] or not body["description"] or not body['price'] or not body['stock'] or not body['category'] or not body['image']:
        return jsonify({'success': False, 'msg': 'missing data'}), 403

    new_product = Product(
        name=body['name'],
        description=body['description'],
        price=body['price'],
        stock=body['stock'],
        category=body['category'],
        image=body['image'],
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"success": True, "data": new_product.serialize()}), 200

# GET A PRODUCT BY HIS ID


@api.route("/product/<int:id>", methods=["GET"])
# @jwt_required()
def get_product(id):
    # user_id = get_jwt_identity()
    # user = db.session.get(User, user_id)

    # if user.role != "admin":
    #   return jsonify({"success": False, "msg": "forbidden"}), 403

    product = db.session.get(Product, id)

    if not product:
        return jsonify({"success": False, "msg": "not found"}), 404

    return jsonify({"success": True, "data": product.serialize()}), 200

# GET ALL PRODUCTS


@api.route("/products", methods=["GET"])
def get_all_products():
    products = db.session.execute(select(Product)).scalars().all()
    transform = [product.serialize() for product in products]
    return jsonify({"success": True, "data": transform}), 200

# UPDATE PRODUCT


@api.route("/product/update/<int:id>", methods=["PUT"])
@jwt_required()
def modify_product(id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if user.role != "admin":
        return jsonify({"success": False, "msg": "forbidden"}), 403

    product = db.session.get(Product, id)

    if not product:
        return jsonify({"success": False, "data": "not found"}), 404

    body = request.get_json()

    product.name = body["name"] if body["name"] else product.name
    product.description = body["description"] if body["description"] else product.description
    product.price = body["price"] if body["price"] else product.price
    product.stock = body["stock"] if body["stock"] else product.stock
    product.category = body["category"] if body["category"] else product.category
    product.image = body["image"] if body["image"] else product.image

    db.session.commit()

    return jsonify({"success": True, "data": product.serialize()})

# DELETE PRODUCT


@api.route("/product/delete/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_product(id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if user.role != "admin":
        return jsonify({"success": False, "msg": "forbidden"}), 403

    product = db.session.get(Product, id)

    if not product:
        return jsonify({"success": False, "msg": "not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"success": True, "data": "product deleted " + str(id)}), 200

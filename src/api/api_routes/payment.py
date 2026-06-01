import os
import stripe  # type: ignore
from flask import request, jsonify  # type: ignore
from api.blueprint import api

from api.models import (
    db,
    User,
    Product,
    Order,
    OrderItem,
    SubscriptionPlan,
    Subscription,
    Payment,
    Cart,
    CartItem,
    PaymentStatus,
)

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from flask_jwt_extended import get_jwt_identity, jwt_required  # type: ignore

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# =========================
# SUBSCRIPTIONS CHECKOUT
# =========================


@api.route("/create-subscription-checkout", methods=["POST"])
@jwt_required()
def create_subscription_checkout():

    try:

        data = request.get_json()

        plan_id = data.get("id")

        user_id = int(get_jwt_identity())

        plan = SubscriptionPlan.query.get(plan_id)

        if not plan:
            return jsonify({"error": "Plan not found"}), 404

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=data.get("email"),
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": plan.name,
                            # "description": plan.description,
                        },
                        "unit_amount": int(plan.price * 100),
                        "recurring": {"interval": "month"},
                    },
                    "quantity": 1,
                }
            ],
            success_url=f"https://ominous-enigma-97r6pr7vprrjc77wq-3000.app.github.dev/successful-payment?planId={plan.id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url="https://ominous-enigma-97r6pr7vprrjc77wq-3000.app.github.dev/payment-error",
            metadata={"plan_id": str(plan.id), "user_id": str(user_id)},
        )

        return jsonify({"url": session.url})

    except Exception as e:
        print("SUBSCRIPTION ERROR:", repr(e))
        return jsonify({"error": str(e)}), 400


# =========================
# NORMAL PRODUCTS CHECKOUT
# =========================


@api.route("/create-checkout-session", methods=["POST"])
@jwt_required()
def create_checkout_session():

    try:

        data = request.get_json()

        products = data.get("products", [])

        user_id = int(get_jwt_identity())

        line_items = []

        total = Decimal("0.00")

        order = Order(
            user_id=user_id,
            total_price=Decimal("0.00"),
            status="pending",
            created_at=datetime.now(timezone.utc),
        )

        db.session.add(order)
        db.session.flush()

        for item in products:

            product_id = int(item["id"])

            product = Product.query.get(product_id)

            if not product:
                return jsonify({"error": "Product not found"}), 404

            quantity = int(item["quantity"])

            if product.stock < quantity:
                return jsonify({"error": "Insufficient stock"}), 400

            subtotal = product.price * quantity
            total += subtotal

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                price=product.price,
            )

            db.session.add(order_item)

            line_items.append(
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": product.name,
                        },
                        "unit_amount": int(product.price * 100),
                    },
                    "quantity": quantity,
                }
            )

        order.total_price = total

        db.session.flush()

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=line_items,
            customer_email=data.get("email"),
            success_url="https://ominous-enigma-97r6pr7vprrjc77wq-3000.app.github.dev/successful-payment",
            cancel_url="https://ominous-enigma-97r6pr7vprrjc77wq-3000.app.github.dev/payment-error",
            metadata={
                "order_id": str(order.id),
            },
        )

        order.stripe_session_id = session.id

        db.session.commit()

        return jsonify({"url": session.url})

    except Exception as e:

        db.session.rollback()

        print("CHECKOUT ERROR:", repr(e))

        return jsonify({"error": str(e)}), 400


# =========================
# STRIPE WEBHOOK
# =========================


@api.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():

    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    sig_header = request.headers.get("Stripe-Signature")

    payload = request.get_data(cache=False)

    try:

        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret)

    except Exception as e:

        return jsonify({"error": str(e)}), 400

    # print("WEBHOOK HIT")
    # print(event["type"])

    if event["type"] != "checkout.session.completed":
        return jsonify({"status": "ignored"}), 200

    session = event["data"]["object"].to_dict()

    # print("EVENT RECEIVED:", event["type"])
    # print("SESSION MODE:", session["mode"])

    # =========================
    # SUBSCRIPTION PAYMENT
    # =========================

    if session["mode"] == "subscription":

        try:

            metadata = session.get("metadata", {})

            user_id = int(metadata["user_id"])

            plan_id = int(metadata["plan_id"])

            stripe_subscription_id = session.get("subscription")

            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                active=True,
                stripe_subscription_id=stripe_subscription_id,
                created_at=datetime.now(timezone.utc),
                cancel_day=datetime.now(timezone.utc) + timedelta(days=30),
            )

            db.session.add(subscription)
            db.session.commit()

            return jsonify({"status": "subscription created"}), 200

        except Exception as e:
            db.session.rollback()
            print("SUBSCRIPTION WEBHOOK ERROR:", repr(e))
            return jsonify({"error": str(e)}), 500
    # =========================
    # NORMAL PAYMENT
    # =========================

    stripe_session_id = session["id"]

    order = Order.query.filter_by(stripe_session_id=stripe_session_id).first()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    order.status = "paid"

    # descontar stock
    for item in order.order_items:

        product = item.product

        product.stock -= item.quantity

    payment = Payment(
        user_id=order.user_id,
        order_id=order.id,
        amount=order.total_price,
        payment_method="stripe",
        status=PaymentStatus.paid,
        stripe_session_id=stripe_session_id,
        created_at=datetime.now(timezone.utc),
    )

    db.session.add(payment)

    cart = Cart(user_id=order.user_id, created_at=datetime.now(timezone.utc))

    db.session.add(cart)

    db.session.flush()

    for item in order.order_items:

        cart_item = CartItem(
            cart_id=cart.id, product_id=item.product_id, quantity=item.quantity
        )

        db.session.add(cart_item)

    db.session.commit()

    return jsonify({"status": "payment success"}), 200

@api.route("/my-subscription", methods=["GET"])
@jwt_required()
def get_my_subscription():
    user_id = get_jwt_identity()

    sub = Subscription.query.filter_by(user_id=user_id, active=True).first()

    if not sub:
        return jsonify({"active": False}), 404

    return jsonify({
        "active": True,
        "planId": sub.plan_id
    }), 200

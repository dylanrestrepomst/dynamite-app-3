import click
from datetime import datetime, timedelta
from decimal import Decimal

from werkzeug.security import generate_password_hash

from api.models import (
    db,
    User,
    Product,
    Order,
    OrderItem,
    SubscriptionPlan,
    Subscription,
    MyPlan,
    DietExerciseType,
    Payment,
    PaymentStatus,
    Cart,
    CartItem,
)


def insert_test_data_logic():
    """Lógica del seed extraída como función reutilizable.
    Se puede llamar desde el comando CLI o desde un endpoint HTTP."""

    print("Resetting and inserting test data...")

    # Delete in FK-safe order.
    db.session.query(CartItem).delete()
    db.session.query(OrderItem).delete()
    db.session.query(Payment).delete()
    db.session.query(MyPlan).delete()
    db.session.query(Cart).delete()
    db.session.query(Subscription).delete()
    db.session.query(Order).delete()
    db.session.query(Product).delete()
    db.session.query(SubscriptionPlan).delete()
    db.session.query(User).delete()
    db.session.commit()

    users = [
        User(
            name="Sofia Martinez",
            email="sofia@example.com",
            password=generate_password_hash("123456"),
            role="admin",
            age=29,
            weight=61.5,
            height=1.65,
            objective="ganar masa muscular",
            photo="https://picsum.photos/seed/sofia/300/300",
            is_active=True,
        ),
        User(
            name="Carlos Gomez",
            email="carlos@example.com",
            password=generate_password_hash("123456"),
            role="user",
            age=34,
            weight=78.0,
            height=1.78,
            objective="definicion",
            photo="https://picsum.photos/seed/carlos/300/300",
            is_active=True,
        ),
        User(
            name="Laura Diaz",
            email="laura@example.com",
            password=generate_password_hash("123456"),
            role="user",
            age=26,
            weight=56.2,
            height=1.62,
            objective="perder grasa",
            photo="https://picsum.photos/seed/laura/300/300",
            is_active=True,
        ),
        User(
            name="Andres Ruiz",
            email="andres@example.com",
            password=generate_password_hash("123456"),
            role="user",
            age=41,
            weight=84.3,
            height=1.82,
            objective="mejorar resistencia",
            photo="https://picsum.photos/seed/andres/300/300",
            is_active=True,
        ),
    ]
    db.session.add_all(users)
    db.session.flush()

    products = []
    categories = ["suplemento", "accesorio", "ropa", "equipo", "snack"]
    for i in range(10):
        products.append(
            Product(
                name=f"Producto {i + 1}",
                description=f"Descripcion del producto {i + 1}",
                price=Decimal(f"{19 + (i * 2)}.99"),
                stock=25 + i,
                category=categories[i % len(categories)],
                image=f"https://picsum.photos/seed/product-{i + 1}/500/500",
            )
        )
    db.session.add_all(products)
    db.session.flush()

    plans = [
        SubscriptionPlan(name="Plan Dieta", price=9.99, description="Plan de alimentacion personalizado de 12 semanas"),
        SubscriptionPlan(name="Plan Ejercicio", price=9.99, description="Plan de entrenamiento de 12 semanas"),
        SubscriptionPlan(name="Plan Completo", price=14.99, description="Plan de dieta y ejercicio personalizado de 12 semanas"),
    ]
    db.session.add_all(plans)
    db.session.flush()

    carts = [Cart(user_id=user.id) for user in users]
    db.session.add_all(carts)
    db.session.flush()

    cart_items = []
    for i in range(10):
        cart_items.append(
            CartItem(
                cart_id=carts[i % len(carts)].id,
                product_id=products[i].id,
                quantity=(i % 3) + 1,
            )
        )
    db.session.add_all(cart_items)
    db.session.flush()

    orders = []
    order_statuses = ["pending", "paid", "cancelled", "shipped"]
    for i in range(10):
        product = products[i]
        qty = (i % 2) + 1
        total_price = (product.price * qty).quantize(Decimal("0.01"))
        orders.append(
            Order(
                user_id=users[i % len(users)].id,
                total_price=total_price,
                status=order_statuses[i % len(order_statuses)],
                created_at=datetime.utcnow() - timedelta(days=i),
            )
        )
    db.session.add_all(orders)
    db.session.flush()

    order_items = []
    for i in range(10):
        product = products[i]
        qty = (i % 2) + 1
        order_items.append(
            OrderItem(
                order_id=orders[i].id,
                product_id=product.id,
                quantity=qty,
                price=product.price,
            )
        )
    db.session.add_all(order_items)
    db.session.flush()

    subscriptions = []
    for i in range(2):
        active = i % 3 != 0
        subscriptions.append(
            Subscription(
                user_id=users[i % len(users)].id,
                plan_id=plans[i].id,
                active=active,
                cancel_day=None if active else datetime.utcnow() - timedelta(days=i),
            )
        )
    db.session.add_all(subscriptions)
    db.session.flush()

    myplans = []
    for i in range(2):
        tipo = DietExerciseType.diet if i % 2 == 0 else DietExerciseType.workout
        myplans.append(
            MyPlan(
                user_id=users[i % len(users)].id,
                plan_id=plans[i].id,
                tipo_plan=tipo,
                plan_data={
                    "week": (i % 4) + 1,
                    "notes": f"Plan personalizado {i + 1}",
                    "calories": 1800 + (i * 50),
                },
            )
        )
    db.session.add_all(myplans)
    db.session.flush()

    payments = []
    methods = ["card", "paypal", "transfer"]
    for i in range(2):
        if i < 5:
            order = orders[i]
            payments.append(
                Payment(
                    user_id=order.user_id,
                    order_id=order.id,
                    subscription_id=None,
                    amount=order.total_price,
                    payment_method=methods[i % len(methods)],
                    status=PaymentStatus.paid,
                    created_at=datetime.utcnow() - timedelta(days=i),
                )
            )
        else:
            subscription = subscriptions[i]
            plan = plans[i]
            payments.append(
                Payment(
                    user_id=subscription.user_id,
                    order_id=None,
                    subscription_id=subscription.id,
                    amount=plan.price,
                    payment_method=methods[i % len(methods)],
                    status=PaymentStatus.paid if subscription.active else PaymentStatus.cancelled,
                    created_at=datetime.utcnow() - timedelta(days=i),
                )
            )

    db.session.add_all(payments)
    db.session.commit()

    return {
        "users": db.session.query(User).count(),
        "products": db.session.query(Product).count(),
        "carts": db.session.query(Cart).count(),
        "cart_items": db.session.query(CartItem).count(),
        "orders": db.session.query(Order).count(),
        "order_items": db.session.query(OrderItem).count(),
        "subscription_plans": db.session.query(SubscriptionPlan).count(),
        "subscriptions": db.session.query(Subscription).count(),
        "myplans": db.session.query(MyPlan).count(),
        "payments": db.session.query(Payment).count(),
    }


def setup_commands(app):

    @app.cli.command("insert-test-users")
    @click.argument("count")
    def insert_test_users(count):
        print("Creating test users")
        for x in range(1, int(count) + 1):
            user = User(
                name=f"Test User {x}",
                email=f"test_user{x}@test.com",
                password=generate_password_hash("123456"),
                role="user",
                age=20 + x,
                weight=65 + x,
                height=1.60 + (x * 0.02),
                objective="mantenimiento",
                photo=f"https://picsum.photos/seed/test-user-{x}/300/300",
                is_active=True,
            )
            db.session.add(user)
            db.session.commit()
            print("User: ", user.email, " created.")
        print("All test users created")

    @app.cli.command("insert-test-data")
    def insert_test_data():
        result = insert_test_data_logic()
        print("Seeder completado:")
        for key, value in result.items():
            print(f"- {key}: {value}")

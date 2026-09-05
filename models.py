from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# =========================================================
# 1. USER MODEL
# =========================================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    # User mobile number
    phone = db.Column(db.String(15), unique=True, nullable=False)

    # Recycler, Buyer, Admin
    role = db.Column(
        db.String(20),
        nullable=False,
        default='Recycler'
    )

    # Reward points earned through recycling
    reward_points = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    # Relationships
    submissions = db.relationship(
        'RecycleSubmission',
        backref='user',
        lazy=True
    )

    orders = db.relationship(
        'Order',
        backref='user',
        lazy=True
    )

    cart_items = db.relationship(
        'Cart',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    wishlist_items = db.relationship(
        'Wishlist',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )


# =========================================================
# 2. PRODUCT MODEL
# =========================================================
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(150),
        nullable=False
    )

    # Books, Plastic, Cardboard, Religious Waste etc.
    category = db.Column(
        db.String(50),
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    image = db.Column(
        db.String(200),
        nullable=False,
        default='default.jpg'
    )

    stock = db.Column(
        db.Integer,
        default=10,
        nullable=False
    )

    # Relationships
    cart_items = db.relationship(
        'Cart',
        backref='product',
        lazy=True
    )

    wishlist_items = db.relationship(
        'Wishlist',
        backref='product',
        lazy=True
    )

    order_items = db.relationship(
        'OrderItem',
        backref='product',
        lazy=True
    )


# =========================================================
# 3. RECYCLE SUBMISSION MODEL
# =========================================================
class RecycleSubmission(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    weight_kg = db.Column(
        db.Float,
        nullable=False
    )

    image = db.Column(
        db.String(200),
        nullable=False
    )

    # Pending, Approved, Rejected
    status = db.Column(
        db.String(20),
        default='Pending',
        nullable=False
    )

    points_awarded = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    date_submitted = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )


# =========================================================
# 4. ORDER MODEL
# =========================================================
class Order(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    # Final amount actually paid after discount
    total_amount = db.Column(
        db.Float,
        nullable=False
    )

    # ---------------- PAYMENT ----------------

    payment_status = db.Column(
        db.String(20),
        default='Pending',
        nullable=False
    )

    payment_method = db.Column(
        db.String(50)
    )

    razorpay_order_id = db.Column(
        db.String(100),
        unique=True
    )

    razorpay_payment_id = db.Column(
        db.String(100),
        unique=True
    )

    razorpay_signature = db.Column(
        db.String(200)
    )

    # ---------------- DELIVERY ----------------

    # Pending Payment, Placed, Shipped,
    # Delivered, Cancelled
    order_status = db.Column(
        db.String(30),
        default='Pending Payment',
        nullable=False
    )

    fullname = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(15),
        nullable=False
    )

    address = db.Column(
        db.Text,
        nullable=False
    )

    city = db.Column(
        db.String(100),
        nullable=False
    )

    state = db.Column(
        db.String(100),
        nullable=False
    )

    pincode = db.Column(
        db.String(10),
        nullable=False
    )

    date_ordered = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationship with OrderItem
    items = db.relationship(
        'OrderItem',
        backref='order',
        lazy=True,
        cascade='all, delete-orphan'
    )


# =========================================================
# 5. ORDER ITEM MODEL
# =========================================================
class OrderItem(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey('order.id'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id'),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    # Product price at the time of purchase
    price = db.Column(
        db.Float,
        nullable=False
    )


# =========================================================
# 6. CART MODEL
# =========================================================
class Cart(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id'),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )


# =========================================================
# 7. WISHLIST MODEL
# =========================================================
class Wishlist(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id'),
        nullable=False
    )
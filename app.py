import os
import time
import requests
import razorpay

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

from models import db, User, Product, RecycleSubmission, Order, Cart, Wishlist, OrderItem

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

MESH_API_KEY = os.getenv("MESH_API_KEY")
MESH_API_URL = os.getenv("MESH_API_URL")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

razorpay_client = None

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
    )

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "Recycler")

        if not username or not email or not phone or not password:
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("register"))

        if not phone.isdigit() or len(phone) != 10:
            flash("Please enter a valid 10-digit mobile number.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return redirect(url_for("register"))

        if role not in ["Recycler", "Buyer"]:
            role = "Recycler"

        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email) |
            (User.phone == phone)
        ).first()

        if existing_user:
            flash("Username, email or mobile number already registered.", "danger")
            return redirect(url_for("register"))

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password=hashed_pw,
            phone=phone,
            role=role,
            reward_points=0
        )

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username, email or mobile number already exists.", "danger")
            return redirect(url_for("register"))

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)

            if user.role == "Admin":
                return redirect(url_for("admin_dashboard"))
            elif user.role == "Recycler":
                return redirect(url_for("recycler_dashboard"))
            else:
                return redirect(url_for("shop"))

        flash("Invalid email or password!", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/recycler/dashboard", methods=["GET", "POST"])
@login_required
def recycler_dashboard():
    if current_user.role != "Recycler":
        return "Access Denied", 403

    if request.method == "POST":
        file = request.files.get("image")

        if not file or file.filename == "":
            flash("Please upload an image.", "danger")
            return redirect(url_for("recycler_dashboard"))

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        category = request.form.get("category", "").strip()

        try:
            weight = float(request.form.get("weight", 0))
        except ValueError:
            weight = 0

        if weight <= 0:
            flash("Please enter a valid waste weight.", "danger")
            return redirect(url_for("recycler_dashboard"))

        estimated_points = int(weight * 10)

        submission = RecycleSubmission(
            user_id=current_user.id,
            category=category,
            weight_kg=weight,
            image=filename,
            status="Pending",
            points_awarded=estimated_points
        )

        db.session.add(submission)
        db.session.commit()

        impact_msg = (
            f"Thank you for recycling {weight} kg of {category}! ♻️ "
            f"Your submission is pending admin approval. "
            f"You can earn approximately {estimated_points} reward points."
        )

        flash(impact_msg, "impact_success")
        return redirect(url_for("recycler_dashboard"))

    history = RecycleSubmission.query.filter_by(
        user_id=current_user.id
    ).order_by(
        RecycleSubmission.date_submitted.desc()
    ).all()

    return render_template("recycler_dash.html", history=history)

@app.route("/shop")
def shop():
    category_filter = request.args.get("category")
    search_query = request.args.get("q")

    query = Product.query

    if category_filter:
        query = query.filter_by(category=category_filter)

    if search_query:
        search_query = search_query.strip()
        query = query.filter(Product.title.ilike(f"%{search_query}%"))

    products = query.order_by(Product.id.desc()).all()

    return render_template("shop.html", products=products)


@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    if product.stock <= 0:
        flash("This product is out of stock.", "warning")
        return redirect(url_for("shop"))

    cart_item = Cart.query.filter_by(
        user_id=current_user.id,
        product_id=product.id
    ).first()

    if cart_item:
        if cart_item.quantity >= product.stock:
            flash("Maximum available stock already added.", "warning")
            return redirect(url_for("shop"))

        cart_item.quantity += 1
    else:
        cart_item = Cart(
            user_id=current_user.id,
            product_id=product.id,
            quantity=1
        )
        db.session.add(cart_item)

    db.session.commit()

    flash(f"{product.title} added to cart!", "success")
    return redirect(url_for("shop"))


@app.route("/cart")
@login_required
def cart():
    cart_items = Cart.query.filter_by(
        user_id=current_user.id
    ).all()

    items = []
    total = 0

    for cart_item in cart_items:
        product = db.session.get(Product, cart_item.product_id)

        if not product:
            db.session.delete(cart_item)
            continue

        subtotal = product.price * cart_item.quantity
        total += subtotal

        items.append({
            "id": cart_item.id,
            "product": product,
            "quantity": cart_item.quantity,
            "subtotal": subtotal
        })

    db.session.commit()

    return render_template(
        "cart.html",
        cart_items=items,
        total=total
    )


@app.route("/remove_cart/<int:id>")
@login_required
def remove_cart(id):
    item = Cart.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(item)
    db.session.commit()

    flash("Item removed from cart.", "success")
    return redirect(url_for("cart"))


@app.route("/increase/<int:id>")
@login_required
def increase(id):
    item = Cart.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    product = db.session.get(Product, item.product_id)

    if not product:
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for("cart"))

    if item.quantity >= product.stock:
        flash("No more stock available.", "warning")
        return redirect(url_for("cart"))

    item.quantity += 1
    db.session.commit()

    return redirect(url_for("cart"))


@app.route("/decrease/<int:id>")
@login_required
def decrease(id):
    item = Cart.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    if item.quantity > 1:
        item.quantity -= 1
    else:
        db.session.delete(item)

    db.session.commit()

    return redirect(url_for("cart"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "Admin":
        return "Access Denied", 403

    submissions = RecycleSubmission.query.filter_by(
        status="Pending"
    ).order_by(
        RecycleSubmission.date_submitted.desc()
    ).all()

    orders = Order.query.order_by(
        Order.date_ordered.desc()
    ).all()

    return render_template(
        "admin_dash.html",
        submissions=submissions,
        orders=orders
    )


@app.route("/admin/approve/<int:sub_id>")
@login_required
def approve_submission(sub_id):
    if current_user.role != "Admin":
        return "Access Denied", 403

    sub = RecycleSubmission.query.get_or_404(sub_id)

    if sub.status != "Pending":
        return redirect(url_for("admin_dashboard"))

    sub.status = "Approved"

    user = db.session.get(User, sub.user_id)

    if user:
        user.reward_points += sub.points_awarded

    db.session.commit()

    flash(
        "Recycling submission approved and reward points added.",
        "success"
    )

    return redirect(url_for("admin_dashboard"))


@app.route("/ecochat")
def ecochat():
    return render_template("ecochat.html")


@app.route("/api/chat", methods=["POST"])
def chat_bot():
    data = request.get_json(silent=True) or {}

    user_message = data.get(
        "message",
        ""
    ).strip()

    if not user_message:
        return jsonify({
            "reply": "Kripya koi message type karein."
        })

    if MESH_API_KEY and MESH_API_URL:
        try:
            headers = {
                "Authorization": f"Bearer {MESH_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "mesh-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are EcoBot, an AI assistant "
                            "for EcoChakra circular economy "
                            "platform. Help users with recycling, "
                            "reward points and eco-products. "
                            "Keep responses helpful, concise "
                            "and friendly."
                        )
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            }

            response = requests.post(
                MESH_API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                res_data = response.json()

                bot_reply = (
                    res_data
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get(
                        "content",
                        "EcoBot response unavailable."
                    )
                )

                return jsonify({
                    "reply": bot_reply
                })

        except Exception as e:
            print("ECOBOT API ERROR:", e)

    msg = user_message.lower()

    if "recycle" in msg or "waste" in msg:
        bot_reply = (
            "Aap EcoChakra par plastic, paper, cardboard "
            "aur other recyclable waste submit karke "
            "reward points earn kar sakte hain! ♻️"
        )
    elif "point" in msg or "reward" in msg:
        bot_reply = (
            "Aap approved recycling submissions se reward "
            "points earn kar sakte hain aur eligible "
            "marketplace purchases par discount use kar sakte hain! 🪙"
        )
    else:
        bot_reply = (
            "Namaste! Main EcoBot hoon. ♻️ "
            "Main recycling, reward points aur "
            "EcoChakra marketplace ke baare mein "
            "aapki help kar sakta hoon."
        )

    return jsonify({
        "reply": bot_reply
    })

@app.route("/create_order", methods=["POST"])
@login_required
def create_order():
    try:
        if not razorpay_client:
            return jsonify({
                "success": False,
                "error": "Razorpay is not configured."
            }), 500

        data = request.get_json(silent=True) or {}

        fullname = data.get("fullname", "").strip()
        phone = data.get("phone", "").strip()
        address = data.get("address", "").strip()
        city = data.get("city", "").strip()
        state = data.get("state", "").strip()
        pincode = data.get("pincode", "").strip()

        if not all([fullname, phone, address, city, state, pincode]):
            return jsonify({
                "success": False,
                "error": "Please fill all delivery details."
            }), 400

        if not phone.isdigit() or len(phone) != 10:
            return jsonify({
                "success": False,
                "error": "Invalid 10-digit phone number."
            }), 400

        if not pincode.isdigit() or len(pincode) != 6:
            return jsonify({
                "success": False,
                "error": "Invalid 6-digit PIN code."
            }), 400

        cart_items = Cart.query.filter_by(
            user_id=current_user.id
        ).all()

        if not cart_items:
            return jsonify({
                "success": False,
                "error": "Your cart is empty."
            }), 400

        total = 0
        valid_cart_items = []

        for cart_item in cart_items:
            product = db.session.get(
                Product,
                cart_item.product_id
            )

            if not product:
                continue

            if cart_item.quantity <= 0 or cart_item.quantity > product.stock:
                return jsonify({
                    "success": False,
                    "error": f"Insufficient stock for {product.title}."
                }), 400

            subtotal = product.price * cart_item.quantity
            total += subtotal

            valid_cart_items.append((cart_item, product))

        if not valid_cart_items:
            return jsonify({
                "success": False,
                "error": "No valid products found in cart."
            }), 400

        if total <= 0:
            return jsonify({
                "success": False,
                "error": "Invalid order amount."
            }), 400

        discount = min(
            current_user.reward_points,
            int(total)
        )

        grand_total = total - discount
        amount_paise = int(round(grand_total * 100))

        if amount_paise <= 0:
            return jsonify({
                "success": False,
                "error": (
                    "Your reward points cover the entire order. "
                    "Online payment cannot be created for ₹0."
                )
            }), 400

        razorpay_order = razorpay_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": (
                f"ecochakra_{current_user.id}_{int(time.time())}"
            ),
            "notes": {
                "user_id": str(current_user.id),
                "customer_name": fullname
            }
        })

        order = Order(
            user_id=current_user.id,
            total_amount=grand_total,
            payment_status="Pending",
            payment_method="Razorpay",
            razorpay_order_id=razorpay_order["id"],
            order_status="Pending Payment",
            fullname=fullname,
            phone=phone,
            address=address,
            city=city,
            state=state,
            pincode=pincode
        )

        db.session.add(order)
        db.session.flush()

        for cart_item, product in valid_cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=cart_item.quantity,
                price=product.price
            )

            db.session.add(order_item)

        db.session.commit()

        return jsonify({
            "success": True,
            "key": RAZORPAY_KEY_ID,
            "amount": amount_paise,
            "currency": "INR",
            "razorpay_order_id": razorpay_order["id"]
        })

    except Exception as e:
        db.session.rollback()

        print("RAZORPAY CREATE ORDER ERROR:", e)

        return jsonify({
            "success": False,
            "error": "Unable to create payment order."
        }), 500


@app.route("/payment/verify", methods=["POST"])
@login_required
def verify_payment():
    try:
        if not razorpay_client:
            return jsonify({
                "success": False,
                "error": "Razorpay is not configured."
            }), 500

        data = request.get_json(silent=True) or {}

        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")

        if not all([
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        ]):
            return jsonify({
                "success": False,
                "error": "Payment information incomplete."
            }), 400

        order = Order.query.filter_by(
            razorpay_order_id=razorpay_order_id,
            user_id=current_user.id
        ).first()

        if not order:
            return jsonify({
                "success": False,
                "error": "Order not found."
            }), 404

        if order.payment_status == "Paid":
            return jsonify({
                "success": True,
                "redirect_url": url_for("payment_success")
            })

        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })

        order_items = OrderItem.query.filter_by(
            order_id=order.id
        ).all()

        for item in order_items:
            product = db.session.get(
                Product,
                item.product_id
            )

            if not product:
                raise Exception("Product no longer exists.")

            if item.quantity > product.stock:
                raise Exception(
                    f"Insufficient stock for {product.title}."
                )

        order.payment_status = "Paid"
        order.payment_method = "Razorpay"
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.order_status = "Placed"

        for item in order_items:
            product = db.session.get(
                Product,
                item.product_id
            )

            product.stock -= item.quantity

        current_cart = Cart.query.filter_by(
            user_id=current_user.id
        ).all()

        original_total = 0

        for cart_item in current_cart:
            product = db.session.get(
                Product,
                cart_item.product_id
            )

            if product:
                original_total += (
                    product.price * cart_item.quantity
                )

        points_used = min(
            current_user.reward_points,
            int(original_total)
        )

        current_user.reward_points = max(
            0,
            current_user.reward_points - points_used
        )

        Cart.query.filter_by(
            user_id=current_user.id
        ).delete(
            synchronize_session=False
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "redirect_url": url_for("payment_success")
        })

    except Exception as e:
        db.session.rollback()

        print("RAZORPAY PAYMENT VERIFICATION ERROR:", e)

        return jsonify({
            "success": False,
            "error": "Payment verification failed."
        }), 400


@app.route("/payment_success")
@login_required
def payment_success():
    return render_template("payment_success.html")


@app.route("/checkout")
@login_required
def checkout():
    cart_items = Cart.query.filter_by(
        user_id=current_user.id
    ).all()

    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("shop"))

    items = []
    total = 0

    for cart_item in cart_items:
        product = db.session.get(
            Product,
            cart_item.product_id
        )

        if not product:
            continue

        subtotal = product.price * cart_item.quantity
        total += subtotal

        items.append({
            "product": product,
            "quantity": cart_item.quantity,
            "subtotal": subtotal
        })

    discount = min(
        current_user.reward_points,
        int(total)
    )

    grand_total = total - discount

    return render_template(
        "checkout.html",
        cart_items=items,
        total=total,
        discount=discount,
        grand_total=grand_total
    )


@app.route("/impact")
def impact_dashboard():
    return render_template("impact_dashboard.html")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
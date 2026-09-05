# EcoChakra ♻️

EcoChakra is an AI-powered circular economy platform designed to encourage recycling, reward users for responsible waste management, and promote sustainable products.

## Features

- User Registration and Login
- Recycler Dashboard
- Waste Submission
- Waste Category and Weight Tracking
- Admin Approval System
- Recycling Reward Points
- Eco-friendly Marketplace
- Product Search and Category Filtering
- Shopping Cart
- Product Stock Management
- Reward Point Discounts
- Razorpay Payment Integration
- Order Management
- EcoBot AI Assistant
- Environmental Impact Dashboard
- Secure Password Hashing
- Role-based Access Control

## Technology Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- Flask-Login
- Flask-Bcrypt
- Tailwind CSS
- JavaScript
- Razorpay
- REST API
- Mesh API
- Gunicorn

## Project Structure

```text
EcoChakra/
│
├── app.py
├── models.py
├── seed_products.py
├── requirements.txt
├── README.md
├── .env
├── .gitignore
│
├── static/
│   ├── images/
│   ├── videos/
│   ├── uploads/
│   └── js/
│
└── templates/
    ├── admin_dash.html
    ├── admin_orders.html
    ├── base.html
    ├── cart.html
    ├── checkout.html
    ├── ecochat.html
    ├── index.html
    ├── login.html
    ├── my_orders.html
    ├── order_details.html
    ├── payment_success.html
    ├── recycler_dash.html
    ├── register.html
    └── shop.html
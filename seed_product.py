from app import app
from models import db, Product

products = [
    {
        "title": "Recycled Paper Notebook",
        "category": "Stationery",
        "price": 149,
        "image": "notebook.jpg",
        "stock": 25
    },
    {
        "title": "Bamboo Toothbrush",
        "category": "Personal Care",
        "price": 99,
        "image": "bamboo-toothbrush.jpg",
        "stock": 30
    },
    {
        "title": "Recycled Plastic Tote Bag",
        "category": "Fashion",
        "price": 249,
        "image": "tote-bag.jpg",
        "stock": 20
    },
    {
        "title": "Recycled Planter",
        "category": "Home & Garden",
        "price": 199,
        "image": "planter.jpg",
        "stock": 15
    },
    {
        "title": "Reusable Water Bottle",
        "category": "Lifestyle",
        "price": 299,
        "image": "water-bottle.jpg",
        "stock": 20
    },
    {
        "title": "Eco Packaging Kit",
        "category": "Packaging",
        "price": 349,
        "image": "eco-packaging.jpg",
        "stock": 15
    },
    {
        "title": "Recycled Glass Candle Holder",
        "category": "Home & Garden",
        "price": 279,
        "image": "candle-holder.jpg",
        "stock": 12
    },
    {
        "title": "Upcycled Denim Pouch",
        "category": "Fashion",
        "price": 179,
        "image": "denim-pouch.jpg",
        "stock": 18
    }
]

with app.app_context():
    db.create_all()

    if Product.query.count() == 0:
        for product_data in products:
            product = Product(**product_data)
            db.session.add(product)

        db.session.commit()
        print("Products added successfully!")
    else:
        print("Products already exist. No changes made.")
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from urllib.parse import quote_plus


# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------

app = FastAPI(title="CompareCart API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# PRODUCT CATEGORIES
# --------------------------------------------------

categories = [
    "Electronics",
    "Mobile Accessories",
    "Computers",
    "Fashion",
    "Footwear",
    "Watches",
    "Bags & Accessories",
    "Gaming",
    "Home & Kitchen",
    "Beauty & Personal Care",
    "Fitness & Sports",
    "Books & Stationery",
    "Pet Supplies",
]


# --------------------------------------------------
# INITIAL PRODUCTS
# --------------------------------------------------

products_db = [
    {
        "id": 1,
        "store": "Amazon",
        "name": "Wireless Headphones",
        "price": 2999,
        "rating": 4.2,
        "category": "Electronics",
        "link": "https://www.amazon.in/s?k=wireless+headphones",
    },
    {
        "id": 2,
        "store": "Flipkart",
        "name": "Running Shoes",
        "price": 1500,
        "rating": 4.5,
        "category": "Footwear",
        "link": "https://www.flipkart.com/search?q=running+shoes",
    },
    {
        "id": 3,
        "store": "Myntra",
        "name": "Cotton T-Shirt",
        "price": 499,
        "rating": 4.0,
        "category": "Fashion",
        "link": "https://www.myntra.com/",
    },
]


# --------------------------------------------------
# SAMPLE PRODUCT CATALOGUE
# --------------------------------------------------

extra_products = [
    ("Amazon", "Smartphone", 14999, 4.3, "Electronics"),
    ("Flipkart", "Bluetooth Speaker", 1999, 4.2, "Electronics"),
    ("Amazon", "Smart TV", 24999, 4.4, "Electronics"),
    ("Flipkart", "Wireless Mouse", 599, 4.1, "Electronics"),
    ("Amazon", "Keyboard", 899, 4.0, "Electronics"),
    ("Flipkart", "Power Bank", 999, 4.2, "Mobile Accessories"),
    ("Amazon", "Mobile Charger", 499, 4.1, "Mobile Accessories"),
    ("Flipkart", "USB Cable", 199, 4.0, "Mobile Accessories"),
    ("Amazon", "Phone Case", 299, 4.2, "Mobile Accessories"),
    ("Flipkart", "Screen Protector", 149, 4.0, "Mobile Accessories"),
    ("Amazon", "Laptop", 45999, 4.4, "Computers"),
    ("Flipkart", "Computer Monitor", 8999, 4.3, "Computers"),
    ("Amazon", "Laptop Stand", 799, 4.1, "Computers"),
    ("Flipkart", "USB Hub", 499, 4.0, "Computers"),
    ("Amazon", "Men's Jeans", 1299, 4.2, "Fashion"),
    ("Myntra", "Women's Dress", 999, 4.3, "Fashion"),
    ("Flipkart", "Hoodie", 799, 4.1, "Fashion"),
    ("Amazon", "Formal Shirt", 899, 4.0, "Fashion"),
    ("Myntra", "Casual Shoes", 1199, 4.2, "Footwear"),
    ("Amazon", "Sports Shoes", 1799, 4.3, "Footwear"),
    ("Flipkart", "Sandals", 499, 4.0, "Footwear"),
    ("Amazon", "Digital Watch", 1499, 4.2, "Watches"),
    ("Flipkart", "Smart Watch", 2499, 4.3, "Watches"),
    ("Amazon", "Leather Wallet", 399, 4.1, "Bags & Accessories"),
    ("Flipkart", "Backpack", 899, 4.2, "Bags & Accessories"),
    ("Amazon", "Gaming Mouse", 1299, 4.4, "Gaming"),
    ("Flipkart", "Gaming Keyboard", 1999, 4.3, "Gaming"),
    ("Amazon", "Gaming Headset", 2499, 4.2, "Gaming"),
    ("Flipkart", "Electric Kettle", 999, 4.1, "Home & Kitchen"),
    ("Amazon", "Mixer Grinder", 2499, 4.3, "Home & Kitchen"),
    ("Flipkart", "Water Bottle", 399, 4.0, "Home & Kitchen"),
    ("Amazon", "Table Lamp", 699, 4.1, "Home & Kitchen"),
    ("Amazon", "Face Wash", 249, 4.2, "Beauty & Personal Care"),
    ("Flipkart", "Moisturizer", 299, 4.1, "Beauty & Personal Care"),
    ("Amazon", "Sunscreen", 399, 4.3, "Beauty & Personal Care"),
    ("Flipkart", "Shampoo", 349, 4.0, "Beauty & Personal Care"),
    ("Amazon", "Yoga Mat", 699, 4.2, "Fitness & Sports"),
    ("Flipkart", "Dumbbells", 1499, 4.3, "Fitness & Sports"),
    ("Amazon", "Resistance Bands", 499, 4.1, "Fitness & Sports"),
    ("Flipkart", "Cricket Bat", 1299, 4.2, "Fitness & Sports"),
    ("Amazon", "Notebook Set", 199, 4.0, "Books & Stationery"),
    ("Flipkart", "Ball Pens", 99, 4.1, "Books & Stationery"),
    ("Amazon", "School Backpack", 799, 4.2, "Books & Stationery"),
    ("Amazon", "Pet Food", 599, 4.3, "Pet Supplies"),
    ("Flipkart", "Pet Bowl", 299, 4.0, "Pet Supplies"),
    ("Amazon", "Pet Toy", 199, 4.1, "Pet Supplies"),
]


# Add sample products after products_db has been created.
for store, name, price, rating, category in extra_products:
    new_id = max(
        (product["id"] for product in products_db),
        default=0,
    ) + 1

    if store == "Amazon":
        link = "https://www.amazon.in/s?k=" + quote_plus(name)
    elif store == "Flipkart":
        link = "https://www.flipkart.com/search?q=" + quote_plus(name)
    else:
        link = "https://www.myntra.com/"

    products_db.append(
        {
            "id": new_id,
            "store": store,
            "name": name,
            "price": float(price),
            "rating": float(rating),
            "category": category,
            "link": link,
        }
    )


# --------------------------------------------------
# DATA MODELS
# --------------------------------------------------

class ProductData(BaseModel):
    store: str
    name: str
    price: float = Field(ge=0)
    rating: float = Field(ge=0, le=5)
    category: str = "Other"
    link: str = ""


class AdminProduct(ProductData):
    pass


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.get("/")
def home():
    index_file = Path(__file__).parent / "index.html"

    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="index.html was not found in the project folder.",
        )

    return FileResponse(index_file)


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# GET ALL CATEGORIES
# --------------------------------------------------

@app.get("/api/categories")
def get_categories():
    return categories


# --------------------------------------------------
# GET PRODUCTS WITH CATEGORY AND SORTING
# --------------------------------------------------

@app.get("/api/products")
def get_products(
    category: Optional[str] = None,
    sort: Optional[str] = None,
    search: Optional[str] = None,
):
    results = products_db.copy()

    if category and category.casefold() != "all":
        results = [
            product
            for product in results
            if product["category"].casefold() == category.casefold()
        ]

    if search:
        search_text = search.casefold()

        results = [
            product
            for product in results
            if search_text in product["name"].casefold()
            or search_text in product["store"].casefold()
            or search_text in product["category"].casefold()
        ]

    if sort == "price_low":
        results.sort(key=lambda product: product["price"])

    elif sort == "price_high":
        results.sort(
            key=lambda product: product["price"],
            reverse=True,
        )

    elif sort == "rating":
        results.sort(
            key=lambda product: product["rating"],
            reverse=True,
        )

    return {
        "count": len(results),
        "products": results,
    }


# --------------------------------------------------
# COMPARE PRODUCT PRICES
# --------------------------------------------------

@app.get("/api/compare")
def compare_products(query: str):
    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a product name.",
        )

    query_text = query.strip().casefold()

    results = [
        product
        for product in products_db
        if query_text in product["name"].casefold()
    ]

    results.sort(key=lambda product: product["price"])

    return {
        "query": query,
        "count": len(results),
        "products": results,
        "message": (
            "Products found."
            if results
            else "No matching products in the sample catalogue."
        ),
    }


# --------------------------------------------------
# ADMIN: VIEW ALL PRODUCTS
# --------------------------------------------------

@app.get("/api/admin/products")
def get_admin_products():
    return products_db


# --------------------------------------------------
# ADMIN: ADD PRODUCT
# --------------------------------------------------

@app.post("/api/admin/add-product")
def add_product(product: AdminProduct):
    new_id = max(
        (item["id"] for item in products_db),
        default=0,
    ) + 1

    new_product = {
        "id": new_id,
        **product.model_dump(),
    }

    products_db.append(new_product)

    return {
        "message": "Product added successfully.",
        "product": new_product,
    }


# --------------------------------------------------
# ADMIN: DELETE PRODUCT
# --------------------------------------------------

@app.delete("/api/admin/delete-product/{product_id}")
def delete_product(product_id: int):
    for index, product in enumerate(products_db):
        if product["id"] == product_id:
            deleted_product = products_db.pop(index)

            return {
                "message": "Product deleted successfully.",
                "product": deleted_product,
            }

    raise HTTPException(
        status_code=404,
        detail="Product not found.",
    )
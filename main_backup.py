import requests
from fastapi.responses import FileResponse
from pathlib import Path
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import quote_plus

app = FastAPI(title="CompareCart API")

# Enable CORS for local frontend development.
# Restrict allowed origins before deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# MOCK DATABASE
# --------------------------------------------------

products_db = [
    {
        "id": 1,
        "store": "Amazon",
        "name": "Wireless Headphones",
        "price": 2999.00,
        "rating": 4.2,
        "link": "https://www.amazon.in/s?k=Wireless+Headphones",
    },
    {
        "id": 2,
        "store": "Flipkart",
        "name": "Running Shoes",
        "price": 1500.00,
        "rating": 4.5,
        "link": "https://www.flipkart.com/search?q=Running+Shoes",
    },
    {
        "id": 3,
        "store": "Myntra",
        "name": "Cotton T-Shirt",
        "price": 499.00,
        "rating": 4.0,
        "link": "https://www.myntra.com/",
    },
]

# --------------------------------------------------
# MODELS
# --------------------------------------------------

class ProductData(BaseModel):
    store: str
    product_name: str
    price: float
    rating: Optional[float] = 0.0
    link: str


class AdminProduct(BaseModel):
    store: str
    name: str
    price: float = Field(ge=0)
    rating: Optional[float] = Field(default=0.0, ge=0, le=5)
    link: str


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/")
async def home():
    return FileResponse(Path(__file__).parent / "index.html")

@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# AMAZON SEARCH
# --------------------------------------------------

def scrape_amazon(query: str):
    products = []

    url = f"https://www.amazon.in/s?k={quote_plus(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=8,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        results = soup.find_all(
            "div",
            {"data-component-type": "s-search-result"},
        )

        for item in results[:5]:
            try:
                heading = item.find("h2")
                name_link = heading.find("a") if heading else None

                if not heading:
                    continue

                name = heading.get_text(" ", strip=True)

                price_element = item.find(
                    "span",
                    class_="a-price-whole",
                )

                if not price_element:
                    continue

                price_text = price_element.get_text(
                    strip=True
                ).replace(",", "").replace(".", "")

                price = float(price_text)

                link = (
                    "https://www.amazon.in"
                    + name_link["href"]
                    if name_link and name_link.get("href")
                    else url
                )

                rating_element = item.find(
                    "span",
                    class_="a-icon-alt",
                )

                rating = 0.0

                if rating_element:
                    rating_text = rating_element.get_text(
                        strip=True
                    )
                    try:
                        rating = float(rating_text.split()[0])
                    except (ValueError, IndexError):
                        pass

                products.append({
                    "store": "Amazon",
                    "name": name,
                    "price": price,
                    "rating": rating,
                    "link": link,
                })

            except (ValueError, TypeError, AttributeError, KeyError):
                continue

    except requests.RequestException:
        # Amazon may block automated requests.
        pass

    return products


# --------------------------------------------------
# FLIPKART SEARCH
# --------------------------------------------------

def scrape_flipkart(query: str):
    products = []

    url = (
        "https://www.flipkart.com/search?q="
        + quote_plus(query)
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=8,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Flipkart changes its HTML structure frequently.
        cards = soup.find_all(
            ["div", "a"],
            class_=[
                "_1AtVbE",
                "_1sdMkc",
                "slAVV4",
                "IRpwTa",
            ],
        )

        seen = set()

        for item in cards:
            try:
                name_element = item.find(
                    ["a", "div"],
                    class_=[
                        "IRpwTa",
                        "KzDlHZ",
                        "wjcEIp",
                    ],
                )

                price_element = item.find(
                    ["div", "div"],
                    class_=[
                        "_30jeq3",
                        "Nx9bqj",
                    ],
                )

                if not name_element or not price_element:
                    continue

                name = name_element.get_text(
                    " ",
                    strip=True,
                )

                price_text = (
                    price_element.get_text(strip=True)
                    .replace("₹", "")
                    .replace(",", "")
                )

                price = float(price_text)

                if not name or name in seen:
                    continue

                seen.add(name)

                anchor = (
                    item
                    if item.name == "a"
                    else item.find("a", href=True)
                )

                link = (
                    "https://www.flipkart.com"
                    + anchor["href"]
                    if anchor and anchor.get("href", "").startswith("/")
                    else url
                )

                products.append({
                    "store": "Flipkart",
                    "name": name,
                    "price": price,
                    "rating": 0.0,
                    "link": link,
                })

                if len(products) >= 5:
                    break

            except (
                ValueError,
                TypeError,
                AttributeError,
                KeyError,
            ):
                continue

    except requests.RequestException:
        # Flipkart may block automated requests.
        pass

    return products


# --------------------------------------------------
# USER API: PRODUCT COMPARISON
# --------------------------------------------------

@app.get("/api/compare")
def compare_products(query: str):
    query = query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query parameter is required",
        )

    # First search the local demo database.
    matches = [
        product.copy()
        for product in products_db
        if query.casefold() in product["name"].casefold()
    ]

    # Search retailer pages if there are no local matches.
    if not matches:
        matches = scrape_amazon(query)
        matches.extend(scrape_flipkart(query))

    # Sort products from lowest price to highest.
    matches.sort(key=lambda product: product["price"])

    return {
        "query": query,
        "count": len(matches),
        "products": matches,
        "message": (
            "No products found. Retailer websites may block "
            "automated searches; try the retailer directly."
            if not matches
            else "Verify prices and availability with the retailer."
        ),
    }


# --------------------------------------------------
# ADMIN API: GET ALL PRODUCTS
# --------------------------------------------------

@app.get("/api/admin/products")
def get_admin_products():
    return products_db


# --------------------------------------------------
# ADMIN API: ADD PRODUCT
# --------------------------------------------------

@app.post("/api/admin/add-product")
def add_product(product: AdminProduct):
    if not product.store.strip():
        raise HTTPException(
            status_code=400,
            detail="Store name is required",
        )

    if not product.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Product name is required",
        )

    new_id = max(
        (item["id"] for item in products_db),
        default=0,
    ) + 1

    new_product = {
        "id": new_id,
        "store": product.store.strip(),
        "name": product.name.strip(),
        "price": product.price,
        "rating": product.rating,
        "link": product.link,
    }

    products_db.append(new_product)

    return {
        "message": "Product added successfully",
        "product": new_product,
    }


# --------------------------------------------------
# ADMIN API: DELETE PRODUCT
# --------------------------------------------------

@app.delete("/api/admin/delete-product/{product_id}")
def delete_product(product_id: int):
    global products_db

    existing_product = next(
        (
            product
            for product in products_db
            if product["id"] == product_id
        ),
        None,
    )

    if existing_product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    products_db = [
        product
        for product in products_db
        if product["id"] != product_id
    ]

    return {
        "message": "Product deleted successfully",
        "id": product_id,
    }


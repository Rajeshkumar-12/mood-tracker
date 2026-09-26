import os
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)

# ============================================================
# DATABASE CONFIGURATION
# ============================================================
# Store database credentials in environment variables only.
# Do not put your real MySQL password in the source code.
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "foodstall")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))

if not MYSQL_PASSWORD:
    print("Warning: MYSQL_PASSWORD environment variable is not set.")


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT
        )
        return connection
    except Error as error:
        print("MySQL connection error:", error)
        return None


def ensure_settings_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key VARCHAR(100) PRIMARY KEY,
            setting_value TEXT NULL
        )
    """)


# ============================================================
# FRONTEND
# ============================================================
@app.route("/")
def home():
    return send_file("Foodstall.html")


@app.route("/payment-qr")
def payment_qr():
    return send_file("GooglePay_QR.png")


# ============================================================
# TEST
# ============================================================
@app.route("/api/test", methods=["GET"])
def api_test():
    return jsonify({
        "success": True,
        "message": "Food Stall API is running"
    })


# ============================================================
# CATEGORIES
# ============================================================
@app.route("/api/categories", methods=["GET"])
def get_categories():
    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, name, created_at
            FROM categories
            ORDER BY id
        """)
        categories = cursor.fetchall()

        return jsonify({
            "success": True,
            "categories": categories
        })

    except Error as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


# ============================================================
# PRODUCTS
# ============================================================
@app.route("/api/products", methods=["GET"])
def get_products():
    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                p.id,
                p.name,
                p.description,
                p.price,
                p.category_id,
                c.name AS category_name,
                p.image,
                p.rating,
                p.is_vegetarian,
                p.is_spicy,
                p.is_popular,
                p.available,
                p.created_at
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.id
        """)

        products = cursor.fetchall()

        for product in products:
            product["price"] = float(product["price"])
            product["rating"] = float(product["rating"])
            product["is_vegetarian"] = bool(product["is_vegetarian"])
            product["is_spicy"] = bool(product["is_spicy"])
            product["is_popular"] = bool(product["is_popular"])
            product["available"] = bool(product["available"])

        return jsonify({
            "success": True,
            "products": products
        })

    except Error as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/products", methods=["POST"])
def create_product():
    data = request.get_json() or {}

    required_fields = ["name", "price"]

    for field in required_fields:
        if field not in data or data[field] in ("", None):
            return jsonify({
                "success": False,
                "message": f"{field} is required"
            }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO products (
                name,
                description,
                price,
                category_id,
                image,
                rating,
                is_vegetarian,
                is_spicy,
                is_popular,
                available
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["name"],
            data.get("description"),
            data["price"],
            data.get("category_id"),
            data.get("image"),
            data.get("rating", 0),
            data.get("is_vegetarian", True),
            data.get("is_spicy", False),
            data.get("is_popular", False),
            data.get("available", True)
        ))

        connection.commit()
        product_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Product created successfully",
            "id": product_id
        }), 201

    except Error as error:
        connection.rollback()
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                p.id,
                p.name,
                p.description,
                p.price,
                p.category_id,
                c.name AS category_name,
                p.image,
                p.rating,
                p.is_vegetarian,
                p.is_spicy,
                p.is_popular,
                p.available,
                p.created_at
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
        """, (product_id,))

        product = cursor.fetchone()

        if not product:
            return jsonify({
                "success": False,
                "message": "Product not found"
            }), 404

        product["price"] = float(product["price"])
        product["rating"] = float(product["rating"])
        product["is_vegetarian"] = bool(product["is_vegetarian"])
        product["is_spicy"] = bool(product["is_spicy"])
        product["is_popular"] = bool(product["is_popular"])
        product["available"] = bool(product["available"])

        return jsonify({
            "success": True,
            "product": product
        })

    except Error as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json() or {}

    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE products
            SET
                name = %s,
                description = %s,
                price = %s,
                category_id = %s,
                image = %s,
                rating = %s,
                is_vegetarian = %s,
                is_spicy = %s,
                is_popular = %s,
                available = %s
            WHERE id = %s
        """, (
            data.get("name"),
            data.get("description"),
            data.get("price"),
            data.get("category_id"),
            data.get("image"),
            data.get("rating", 0),
            data.get("is_vegetarian", True),
            data.get("is_spicy", False),
            data.get("is_popular", False),
            data.get("available", True),
            product_id
        ))

        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Product not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Product updated successfully"
        })

    except Error as error:
        connection.rollback()
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM products WHERE id = %s",
            (product_id,)
        )
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Product not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Product deleted successfully"
        })

    except Error as error:
        connection.rollback()

        return jsonify({
            "success": False,
            "message": (
                "Product could not be deleted. "
                "It may already be used in an order."
            ),
            "error": str(error)
        }), 400

    finally:
        cursor.close()
        connection.close()


# ============================================================
# REGISTER
# ============================================================
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "Name, email and password are required"
        }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Email already registered"
            }), 409

        cursor.execute("""
            INSERT INTO users
            (name, email, phone, password, role)
            VALUES (%s, %s, %s, %s, 'customer')
        """, (
            name,
            email,
            phone,
            password
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Registration successful"
        }), 201

    except Error as error:
        connection.rollback()

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


# ============================================================
# LOGIN
# ============================================================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, name, email, phone, password, role
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

        if not user or user["password"] != password:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        user.pop("password", None)

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user
        })

    except Error as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


# ============================================================
# ORDERS
# ============================================================
@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json() or {}

    customer_name = data.get("customer_name")
    phone = data.get("phone")
    address = data.get("address")
    payment_method = data.get("payment_method", "Cash on Delivery")
    user_id = data.get("user_id")
    items = data.get("items", [])

    if not customer_name or not phone or not address:
        return jsonify({
            "success": False,
            "message": "Customer name, phone and address are required"
        }), 400

    if not items:
        return jsonify({
            "success": False,
            "message": "Order must contain at least one item"
        }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        # Recalculate the order total from database prices.
        calculated_subtotal = 0
        validated_items = []

        for item in items:
            product_id = item.get("product_id")
            quantity = int(item.get("quantity", 0))

            if not product_id or quantity <= 0:
                return jsonify({
                    "success": False,
                    "message": "Invalid order item"
                }), 400

            cursor.execute("""
                SELECT id, name, price, available
                FROM products
                WHERE id = %s
            """, (product_id,))

            product = cursor.fetchone()

            if not product:
                return jsonify({
                    "success": False,
                    "message": f"Product {product_id} not found"
                }), 400

            if not product["available"]:
                return jsonify({
                    "success": False,
                    "message": f'{product["name"]} is currently unavailable'
                }), 400

            price = float(product["price"])
            subtotal = price * quantity
            calculated_subtotal += subtotal

            validated_items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "quantity": quantity,
                "price": price,
                "subtotal": subtotal
            })

        # Keep the existing delivery-fee behavior.
        delivery_fee = 40 if calculated_subtotal < 300 else 0
        total_amount = calculated_subtotal + delivery_fee

        # Generate a 6-digit delivery OTP.
        import random
        delivery_otp = str(random.randint(100000, 999999))

        cursor.execute("""
            INSERT INTO orders (
                user_id,
                customer_name,
                phone,
                address,
                total_amount,
                payment_method,
                status,
                delivery_otp,
                otp_verified
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending', %s, FALSE)
        """, (
            user_id,
            customer_name,
            phone,
            address,
            total_amount,
            payment_method,
            delivery_otp
        ))

        order_id = cursor.lastrowid

        for item in validated_items:
            cursor.execute("""
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    product_name,
                    quantity,
                    price,
                    subtotal
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                item["product_id"],
                item["product_name"],
                item["quantity"],
                item["price"],
                item["subtotal"]
            ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Order placed successfully",
            "order_id": order_id,
            "subtotal": round(calculated_subtotal, 2),
            "delivery_fee": delivery_fee,
            "total_amount": round(total_amount, 2),
            "delivery_otp": delivery_otp
        }), 201

    except (Error, ValueError) as error:
        connection.rollback()

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/orders/customer/<int:user_id>", methods=["GET"])
def get_customer_orders(user_id):
    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                o.id,
                o.user_id,
                o.customer_name,
                o.phone,
                o.address,
                o.total_amount,
                o.payment_method,
                o.status,
                o.delivery_otp,
                o.otp_verified,
                o.delivered_at,
                o.created_at
            FROM orders o
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
        """, (user_id,))

        orders = cursor.fetchall()

        for order in orders:
            order["total_amount"] = float(order["total_amount"])
            order["otp_verified"] = bool(order["otp_verified"])

        return jsonify({
            "success": True,
            "orders": orders
        })

    except Error as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/orders", methods=["GET"])
def get_orders():
    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                o.id,
                o.user_id,
                o.customer_name,
                o.phone,
                o.address,
                o.total_amount,
                o.payment_method,
                o.status,
                o.otp_verified,
                o.delivered_at,
                o.created_at
            FROM orders o
            ORDER BY o.created_at DESC
        """)

        orders = cursor.fetchall()

        for order in orders:
            order["total_amount"] = float(order["total_amount"])
            order["otp_verified"] = bool(order["otp_verified"])

        return jsonify({
            "success": True,
            "orders": orders
        })

    except Error as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                user_id,
                customer_name,
                phone,
                address,
                total_amount,
                payment_method,
                status,
                delivery_otp,
                otp_verified,
                delivered_at,
                created_at
            FROM orders
            WHERE id = %s
        """, (order_id,))

        order = cursor.fetchone()

        if not order:
            return jsonify({
                "success": False,
                "message": "Order not found"
            }), 404

        cursor.execute("""
            SELECT
                id,
                product_id,
                product_name,
                quantity,
                price,
                subtotal
            FROM order_items
            WHERE order_id = %s
            ORDER BY id
        """, (order_id,))

        items = cursor.fetchall()

        order["total_amount"] = float(order["total_amount"])
        order["otp_verified"] = bool(order["otp_verified"])

        for item in items:
            item["price"] = float(item["price"])
            item["subtotal"] = float(item["subtotal"])

        order["items"] = items

        return jsonify({
            "success": True,
            "order": order
        })

    except Error as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    data = request.get_json() or {}
    status = data.get("status")
    otp = str(data.get("otp", "")).strip()

    allowed_statuses = {
        "Pending",
        "Confirmed",
        "Preparing",
        "Ready",
        "Out for Delivery",
        "Delivered",
        "Cancelled"
    }

    if status not in allowed_statuses:
        return jsonify({
            "success": False,
            "message": "Invalid order status"
        }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, status, delivery_otp, otp_verified
            FROM orders
            WHERE id = %s
        """, (order_id,))

        order = cursor.fetchone()

        if not order:
            return jsonify({
                "success": False,
                "message": "Order not found"
            }), 404

        # Delivery verification is required before marking an order Delivered.
        if status == "Delivered":
            if order["otp_verified"]:
                pass
            elif not otp:
                return jsonify({
                    "success": False,
                    "message": "Delivery OTP is required before marking this order as Delivered"
                }), 400
            elif otp != str(order["delivery_otp"]):
                return jsonify({
                    "success": False,
                    "message": "Incorrect delivery OTP"
                }), 400
            else:
                cursor.execute("""
                    UPDATE orders
                    SET
                        status = 'Delivered',
                        otp_verified = TRUE,
                        delivered_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (order_id,))

                connection.commit()

                return jsonify({
                    "success": True,
                    "message": "Order delivered successfully"
                })

        cursor.execute("""
            UPDATE orders
            SET status = %s
            WHERE id = %s
        """, (status, order_id))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Order status updated successfully"
        })

    except Error as error:
        connection.rollback()

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/orders/<int:order_id>/cancel", methods=["PUT"])
def cancel_customer_order(order_id):
    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"success": False, "message": "Login is required to cancel an order"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, status
            FROM orders
            WHERE id = %s AND user_id = %s
        """, (order_id, user_id))
        order = cursor.fetchone()

        if not order:
            return jsonify({"success": False, "message": "Order not found"}), 404
        if order["status"] not in {"Pending", "Confirmed"}:
            return jsonify({
                "success": False,
                "message": "This order can no longer be cancelled"
            }), 400

        cursor.execute(
            "UPDATE orders SET status = 'Cancelled' WHERE id = %s",
            (order_id,)
        )
        connection.commit()
        return jsonify({"success": True, "message": "Order cancelled successfully"})
    except Error as error:
        connection.rollback()
        return jsonify({"success": False, "message": str(error)}), 500
    finally:
        cursor.close()
        connection.close()


# ============================================================
# ADMIN STATS
# ============================================================
@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'customer'")
        customers = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM products")
        products = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM orders")
        orders = cursor.fetchone()["count"]

        date_value = request.args.get("date", "").strip()
        date_filter = ""
        params = []
        if date_value:
            try:
                datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                return jsonify({"success": False, "message": "Date must be YYYY-MM-DD"}), 400
            date_filter = " AND DATE(created_at) = %s"
            params.append(date_value)

        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS revenue
            FROM orders
            WHERE status != 'Cancelled'""" + date_filter, params)
        revenue = float(cursor.fetchone()["revenue"])

        return jsonify({
            "success": True,
            "stats": {
                "customers": customers,
                "products": products,
                "orders": orders,
                "revenue": revenue
            }
        })

    except Error as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/settings/payment", methods=["GET"])
def get_payment_settings():
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)
    try:
        ensure_settings_table(cursor)
        cursor.execute("""
            SELECT setting_key, setting_value
            FROM app_settings
            WHERE setting_key IN ('upi_id', 'upi_qr_url')
        """)
        settings = {row["setting_key"]: row["setting_value"] or "" for row in cursor.fetchall()}
        connection.commit()
        return jsonify({
            "success": True,
            "upi_id": settings.get("upi_id", ""),
            "upi_qr_url": settings.get("upi_qr_url", "")
        })
    except Error as error:
        connection.rollback()
        return jsonify({"success": False, "message": str(error)}), 500
    finally:
        cursor.close()
        connection.close()


@app.route("/api/settings/payment", methods=["PUT"])
def save_payment_settings():
    data = request.get_json() or {}
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor()
    try:
        ensure_settings_table(cursor)
        for key, value in {
            "upi_id": str(data.get("upi_id", "")).strip(),
            "upi_qr_url": str(data.get("upi_qr_url", "")).strip()
        }.items():
            cursor.execute("""
                INSERT INTO app_settings (setting_key, setting_value)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
            """, (key, value))
        connection.commit()
        return jsonify({"success": True, "message": "Payment settings saved"})
    except Error as error:
        connection.rollback()
        return jsonify({"success": False, "message": str(error)}), 500
    finally:
        cursor.close()
        connection.close()


# ============================================================
# CUSTOMERS
# ============================================================
@app.route("/api/customers", methods=["GET"])
def get_customers():
    connection = get_db_connection()

    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                u.phone,
                u.role,
                u.created_at,
                COUNT(o.id) AS order_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.role = 'customer'
            GROUP BY
                u.id,
                u.name,
                u.email,
                u.phone,
                u.role,
                u.created_at
            ORDER BY u.created_at DESC
        """)

        customers = cursor.fetchall()

        return jsonify({
            "success": True,
            "customers": customers
        })

    except Error as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        cursor.close()
        connection.close()


# ============================================================
# START SERVER
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

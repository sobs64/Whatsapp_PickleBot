from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_orders():
    conn = sqlite3.connect("swad_orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_number, flavour, quantity FROM orders")
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.route("/")
def index():
    orders = get_orders()

    # Total orders
    total_orders = len(orders)

    # Unique users
    unique_users = len(set([row[1] for row in orders]))

    # Total quantity (make sure to cast to int)
    total_quantity = sum([int(row[3]) for row in orders if row[3].isdigit()])

    # Most ordered flavour
    flavour_counts = {}
    for row in orders:
        flavour = row[2]
        qty = int(row[3]) if str(row[3]).isdigit() else 0
        flavour_counts[flavour] = flavour_counts.get(flavour, 0) + qty

    most_ordered_flavour = max(flavour_counts, key=flavour_counts.get) if flavour_counts else "N/A"

    return render_template(
        "orders.html",
        orders=orders,
        total_orders=total_orders,
        unique_users=unique_users,
        total_quantity=total_quantity,
        most_ordered_flavour=most_ordered_flavour
    )

if __name__ == "__main__":
    app.run(debug=True, port=5001)

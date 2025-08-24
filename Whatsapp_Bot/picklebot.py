import os
import requests
import logging
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
load_dotenv()
# --------------------------
# Setup
# --------------------------
logging.basicConfig(level=logging.INFO)

ACCESS_TOKEN = os.getenv("WA_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN")

if not all([ACCESS_TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN]):
    logging.warning("WA_ACCESS_TOKEN/WA_PHONE_NUMBER_ID/WA_VERIFY_TOKEN not set. Set env vars before running.")

app = Flask(__name__)

# --------------------------
# Database Setup (New DB)
# --------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "swad_orders.db")

engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_number = Column(String, nullable=False)
    flavour = Column(String, nullable=False)
    quantity = Column(String, nullable=False)

Base.metadata.create_all(engine)
logging.info(f"Database ready at: {DB_PATH}")

# --------------------------
# User State
# --------------------------
user_state = {}  # {user_number: {"cart": [{"flavour": , "quantity": }], "current": {}}}

# --------------------------
# Helpers
# --------------------------
def send_text(to, text):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    r = requests.post(url, headers=headers, json=payload)
    logging.info(f"Text sent: {r.status_code} {r.text}")

def send_list(to, text, button_text, options, section_title="Options"):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": text},
            "action": {
                "button": button_text,
                "sections": [
                    {
                        "title": section_title,
                        "rows": [{"id": opt_id, "title": opt_title} for opt_id, opt_title in options]
                    }
                ]
            }
        }
    }
    r = requests.post(url, headers=headers, json=payload)
    logging.info(f"List sent: {r.status_code} {r.text}")

# --------------------------
# Webhook Verify (Working version)
# --------------------------
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

# --------------------------
# Webhook Messages
# --------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    logging.info(f"Incoming webhook: {data}")

    try:
        if "messages" in data["entry"][0]["changes"][0]["value"]:
            msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
            from_number = msg["from"]

            if from_number not in user_state:
                user_state[from_number] = {"cart": [], "current": {}}

            state = user_state[from_number]

            # Interactive messages
            if msg.get("type") == "interactive":
                interactive = msg["interactive"]
                if interactive["type"] == "list_reply":
                    button_id = interactive["list_reply"]["id"]

                    if button_id.startswith("flavour_"):
                        flavour = button_id.split("_")[1]
                        state["current"] = {"flavour": flavour}
                        send_list(
                            from_number,
                            f"You chose {flavour.title()} pickle. Select quantity:",
                            "Pick quantity",
                            [("qty_150", "150 gm"), ("qty_250", "250 gm"), ("qty_500", "500 gm")],
                            section_title="Quantities"
                        )

                    elif button_id.startswith("qty_"):
                        qty = button_id.split("_")[1]
                        state["current"]["quantity"] = qty
                        flavour = state["current"]["flavour"]

                        send_list(
                            from_number,
                            f"You added {flavour.title()} pickle - {qty} gm to your cart.",
                            "Next action",
                            [("add_more", "Add More"), ("checkout", "Checkout"), ("restart", "Restart")],
                            section_title="Cart Actions"
                        )

                    elif button_id == "add_more":
                        if state["current"]:
                            state["cart"].append(state["current"])
                            state["current"] = {}
                        send_list(
                            from_number,
                            "Choose your pickle flavour to add:",
                            "Pick a flavour",
                            [
                                ("flavour_onion", "Onion Pickle"),
                                ("flavour_carrot", "Carrot Pickle"),
                                ("flavour_greenchilli", "Green Chilli Pickle"),
                                ("flavour_amla", "Amla Pickle")
                            ],
                            section_title="Flavours"
                        )

                    elif button_id == "checkout":
                        if state["current"]:
                            state["cart"].append(state["current"])
                            state["current"] = {}
                        summary_lines = [f"{idx}. {item['flavour'].title()} - {item['quantity']} gm"
                                         for idx, item in enumerate(state["cart"], start=1)]
                        summary_text = "Your Cart:\n" + "\n".join(summary_lines)
                        send_list(
                            from_number,
                            summary_text,
                            "Finalize Order",
                            [("confirm_order", "Confirm"), ("restart", "Restart")],
                            section_title="Finalize"
                        )

                    elif button_id == "confirm_order":
                        session = Session()
                        try:
                            for item in state["cart"]:
                                if not all([item.get("flavour"), item.get("quantity")]):
                                    continue
                                new_order = Order(
                                    user_number=from_number,
                                    flavour=item["flavour"],
                                    quantity=item["quantity"]
                                )
                                session.add(new_order)
                            session.commit()
                            send_text(from_number, "Thank you for shopping with Swad! Your order has been placed.")
                            send_text(from_number, 'Type "Hi" or "start" to shop again')
                            user_state.pop(from_number, None)
                        except Exception as e:
                            session.rollback()
                            logging.error(f"Failed to save order: {e}")
                            send_text(from_number, "Something went wrong while placing your order. Please try again.")
                        finally:
                            session.close()

                    elif button_id == "restart":
                        user_state.pop(from_number, None)
                        send_list(
                            from_number,
                            "Let's start again! Choose your pickle flavour:",
                            "Pick a flavour",
                            [
                                ("flavour_onion", "Onion Pickle"),
                                ("flavour_carrot", "Carrot Pickle"),
                                ("flavour_greenchilli", "Green Chilli Pickle"),
                                ("flavour_amla", "Amla Pickle")
                            ],
                            section_title="Flavours"
                        )

            # Text messages
            elif msg.get("type") == "text":
                body = msg["text"]["body"].lower()
                if "hi" in body or "start" in body:
                    user_state[from_number] = {"cart": [], "current": {}}
                    send_text(from_number, "Welcome to Swad Homemade Pickles!")
                    send_list(
                        from_number,
                        "Choose your pickle flavour:",
                        "Pick a flavour",
                        [
                            ("flavour_onion", "Onion Pickle"),
                            ("flavour_carrot", "Carrot Pickle"),
                            ("flavour_greenchilli", "Green Chilli Pickle"),
                            ("flavour_amla", "Amla Pickle")
                        ],
                        section_title="Flavours"
                    )

    except Exception as e:
        logging.error(f"Error handling message: {e}")

    return jsonify({"status": "ok"}), 200

# --------------------------
# Run App
# --------------------------
if __name__ == "__main__":
    app.run(port=5000, debug=False)

#Swad Homemade Pickles WhatsApp Bot & Dashboard

A WhatsApp bot for **Swad Homemade Pickles** that allows users to place orders and a dashboard to view order history and analytics.

**Backend Bot**: picklebot.py

**Frontend Dashboard**: app.py

**Database**: SQLite (swad_orders.db)

##Tech Stack##

**Frontend**: Flask (Python), HTML/CSS, Chart.js

**Backend**: Python, Flask, Requests, SQLAlchemy

**Database**: SQLite

##Database Schema Summary##

orders(id(pk), user_number, flavour, quantity)

##Getting Started##
**1. Clone the Repository**
git clone <your-repo-url>
cd WhatsappBot

**2. Setup Environment Variables**

Create a .env file in the project root:

WA_ACCESS_TOKEN=<your-whatsapp-cloud-access-token>
WA_PHONE_NUMBER_ID=<your-phone-number-id>
WA_VERIFY_TOKEN=<your-verify-token>

**3. Install Dependencies**
pip install flask sqlalchemy requests python-dotenv

**4. Setup Database**

The bot automatically creates swad_orders.db with the orders table.
No manual SQL setup is required.

**5. Running the WhatsApp Bot**
python picklebot.py


Start ngrok to expose your local server:

ngrok http 5000


Copy the HTTPS URL from ngrok and set it as Webhook URL in Meta Developer Portal → WhatsApp → Webhooks
.

Verify token must match WA_VERIFY_TOKEN in .env.

Subscribe to messages and message_status fields.

**6. Running the Frontend Dashboard**
python app.py


Open in browser:

http://127.0.0.1:5001/


Dashboard displays:

Order History Table

Analytics Charts (Orders per flavour & quantity)

Make sure orders.html is in the templates/ folder for Flask to render the dashboard.

**7. Using the Bot**

Send Hi or start to your WhatsApp sandbox number.

Bot will show pickle flavours, quantity options, and cart actions.

Confirm order → saved in swad_orders.db.

Restart anytime using the interactive options.

**8. Database Access**

You can view all orders directly using SQLite:

sqlite3 swad_orders.db


Example query:

SELECT * FROM orders;

**9. Troubleshooting**

Webhook Verification Failed

Ensure VERIFY_TOKEN matches between .env and Meta portal.

Ngrok URL must be HTTPS and running.

Bot Not Responding

Flask app must be running.

Ngrok tunnel must be active.

Check console logs for errors.

Orders Not Saving

Check database path in picklebot.py.


Ensure SQLite file is writable.

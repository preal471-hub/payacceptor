import telebot
import json
import os
import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [1874506198, 987525815]

CHANNEL_LINK = "https://t.me/+bhQASTa4hSE1MjVl"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

USERS_FILE = "users.json"
PAY_FILE = "payments.json"

PLANS = {
    "monthly": "₹2,499",
    "quarterly": "₹4,499",
    "yearly": "₹6,499"
}

# ---------------- FILE SETUP ----------------

for file in [USERS_FILE, PAY_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)


def load(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}


def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)


# ---------------- SAVE USER ----------------

def save_user(user_id):
    user_id = str(user_id)

    users = load(USERS_FILE)

    if user_id not in users:
        users[user_id] = True
        save(USERS_FILE, users)


# ---------------- UTR VALIDATOR ----------------

def is_valid_utr(text):

    patterns = [
        r'^\d{12}$',
        r'^\d{13}$',
        r'^\d{16}$',
        r'^[A-Z]{4}\d{7,12}$',
        r'^\d{6,12}$'
    ]

    for p in patterns:
        if re.match(p, text):
            return True

    return False


# ================= START =================

@bot.message_handler(commands=['start'])
def start(msg):

    save_user(msg.from_user.id)

    text = (
        "🎉 <b>Crude Oil OPTION Trades</b>\n"
        "🎉 <b>Natural Gas OPTION Trades</b>\n\n"
        "💰 Earn up to ₹4,000 – ₹6,000 Daily\n\n"
        "📈 Monthly Capture\n"
        "1000 – 1500 Points in Options\n\n"
        "🎯 Perfect Entries with Targets & Minimum SL\n\n"
        "📊 All Trades Intraday\n"
        "(No Overnight Holding)\n\n"
        "🔥 Accuracy up to 99%\n\n"
        "👨‍🏫 Live Trade Support & Proper Guidance\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💎 <b>VIP Subscription Plans</b>\n\n"
        "📅 Monthly – ₹2,499\n"
        "⏳ Quarterly – ₹4,499\n"
        "🏆 Yearly – ₹6,499\n\n"
        "Select your plan below 👇"
    )

    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton("📅 Monthly – ₹2,499", callback_data="plan_monthly"))
    markup.add(InlineKeyboardButton("⏳ Quarterly – ₹4,499", callback_data="plan_quarterly"))
    markup.add(InlineKeyboardButton("🏆 Yearly – ₹6,499", callback_data="plan_yearly"))

    bot.send_message(msg.chat.id, text, reply_markup=markup)


# ================= PLAN CLICK =================

@bot.callback_query_handler(func=lambda call: call.data.startswith("plan_"))
def plan_selected(call):

    bot.answer_callback_query(call.id)

    user_id = str(call.from_user.id)
    plan = call.data.split("_")[1]
    amount = PLANS[plan]

    payments = load(PAY_FILE)

    payments[user_id] = {
        "plan": plan,
        "amount": amount,
        "status": "awaiting_payment"
    }

    save(PAY_FILE, payments)

    caption = (
        f"💳 <b>Payment Information</b>\n\n"
        f"Plan: <b>{plan.capitalize()}</b>\n"
        f"Amount: <b>{amount}</b>\n\n"
        f"📍 <b>UPI ID</b>\n"
        f"<code>paytmqr281005050101sxxhellw7don@paytm</code>\n\n"
        f"After payment send your UTR number and link given to you automatically."
    )

    bot.send_photo(call.message.chat.id, open("qr.png", "rb"), caption=caption)


# ================= RECEIVE UTR =================

@bot.message_handler(func=lambda m: not m.text.startswith("/"))
def receive_utr(msg):

    user_id = str(msg.from_user.id)
    text = msg.text.strip()

    payments = load(PAY_FILE)

    if user_id not in payments:
        return

    if payments[user_id]["status"] != "awaiting_payment":
        return

    if not is_valid_utr(text):

        bot.reply_to(
            msg,
            "❌ Invalid UTR number.\n\nPlease complete payment and send valid UTR."
        )
        return

    payments[user_id]["utr"] = text
    payments[user_id]["status"] = "pending"

    save(PAY_FILE, payments)

    bot.send_message(user_id, "⏳ Payment under verification")

    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

    for admin in ADMIN_IDS:
        try:
            bot.send_message(
                admin,
                f"💰 Payment Request\n\n"
                f"User: {user_id}\n"
                f"Plan: {payments[user_id]['plan']}\n"
                f"Amount: {payments[user_id]['amount']}\n"
                f"UTR: {text}",
                reply_markup=markup
            )
        except:
            pass


# ================= APPROVE =================

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve"))
def approve(call):

    admin_id = call.from_user.id
    user_id = call.data.split("_")[1]

    payments = load(PAY_FILE)

    payments[user_id]["status"] = "approved"

    save(PAY_FILE, payments)

    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton("🚀 Join VIP Channel", url=CHANNEL_LINK))

    bot.send_message(
        user_id,
        "✅ Payment Approved!\nClick below to join VIP channel.",
        reply_markup=markup
    )

    bot.answer_callback_query(call.id, "Link sent")

    bot.send_message(admin_id, f"✅ Approved\n\nUser: {user_id}\nVIP link sent.")


# ================= REJECT =================

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject"))
def reject(call):

    admin_id = call.from_user.id
    user_id = call.data.split("_")[1]

    payments = load(PAY_FILE)

    payments[user_id]["status"] = "rejected"

    save(PAY_FILE, payments)

    bot.send_message(user_id, "❌ Payment not found")

    bot.answer_callback_query(call.id, "Link not sent")

    bot.send_message(admin_id, f"❌ Rejected\n\nUser: {user_id}\nVIP link not sent.")


# ================= BROADCAST =================

@bot.message_handler(commands=['broadcast'])
def broadcast(msg):

    if msg.from_user.id not in ADMIN_IDS:
        return

    text = msg.text.replace("/broadcast", "").strip()

    if not text:
        bot.reply_to(msg, "Use:\n/broadcast your message")
        return

    users = load(USERS_FILE)

    sent = 0
    failed = 0

    for user in users:

        try:
            bot.send_message(int(user), text)
            sent += 1
        except:
            failed += 1

    bot.reply_to(msg, f"Broadcast done\nSent: {sent}\nFailed: {failed}")


# ================= KEEP ALIVE =================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot running"


threading.Thread(
    target=lambda: app.run(host="0.0.0.0", port=10000)
).start()


bot.infinity_polling(skip_pending=True)


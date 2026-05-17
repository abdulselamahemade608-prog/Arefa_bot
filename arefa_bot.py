import telebot
from telebot import types
import datetime
import time 

# --- 1. CONFIGURATION ---
TOKEN = "8747436808:AAF_HymQC0SeHM8u05AiQ3zHWCpYuZIvpZY"
ADMIN_IDS = [7975950709,7725001366] 
CHANNELS = ["@Felafel_arafa_12"]

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- 2. DATABASE (Memory-based) ---
prices = {"super": 150, "special": 100, "normal": 70}
delivery_guys = [8192973594] 
bank_accounts = {
    "telebirr": {"name": "Telebirr", "acc": "", "owner": ""}
}
sales_status = {"is_open": False, "reason": "Not started yet"}
daily_report = {"total_sales": 0, "orders_count": 0}
all_users = set()
orders_db = {} 
user_spam = {} 
active_delivery_msgs = {} 

# --- 3. HELPER FUNCTIONS ---
def is_subscribed(u_id):
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch, u_id).status
            if status in ['left', 'kicked', 'None']: return False
        except Exception as e:
            return False
    return True

def is_blocked(u_id):
    if u_id in user_spam:
        count, last_t = user_spam[u_id]
        if count >= 5 and (time.time() - last_t) < 172800:
            return True
    return False

# --- 4. MAIN MENU ---
@bot.message_handler(commands=['start'])
def start(message):
    all_users.add(message.chat.id)
    if is_blocked(message.from_user.id):
        bot.send_message(message.chat.id, "❌ <b>Blocked: Too many invalid attempts. Try again in 48h.</b>")
        return
    
    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        for ch in CHANNELS:
            ch_name = ch.replace("@", "")
            btn = types.InlineKeyboardButton("Join Channel 📢", url=f"https://t.me/{ch_name}")
            markup.add(btn)
        check_btn = types.InlineKeyboardButton("Joined ✅", callback_data="check_sub")
        markup.add(check_btn)
        
        photo_url = "https://t.me/ISATBIRR1992/2" 
        
        try:
            bot.send_photo(message.chat.id, photo_url, caption="<b>Welcome! Please join our channels first:</b>", reply_markup=markup)
        except:
            bot.send_message(message.chat.id, "<b>Welcome! Please join our channels first:</b>", reply_markup=markup)
    else:
        main_menu(message)

def main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Normal Ertib", "Special Ertib", "Super Ertib")
    markup.add("Developer")
    bot.send_message(message.chat.id, "<b>Welcome! Select your order:</b>", reply_markup=markup)

# --- 5. ORDER PROCESS ---
@bot.message_handler(func=lambda m: m.text in ["Normal Ertib", "Special Ertib", "Super Ertib"])
def choice_usage(message):
    if not is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "❌ <b>Please join the channels first! /start</b>")
        return
    if not sales_status["is_open"]:
        bot.send_message(message.chat.id, f"⚠️ <b>Shop is Closed.</b>\nReason: {sales_status['reason']}")
        return
    
    item = "super" if "Super" in message.text else "special" if "Special" in message.text else "normal"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Takeaway (Delivery)", "Dine-in (At Hotel)")
    markup.add("🔙 Back")
    msg = bot.send_message(message.chat.id, "<b>Choose service type:</b>", reply_markup=markup)
    bot.register_next_step_handler(msg, get_qty, item)

def get_qty(message, item):
    if message.text == "🔙 Back": return main_menu(message)
    usage = "Takeaway" if "Takeaway" in message.text else "Dine-in"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔙 Back")
    msg = bot.send_message(message.chat.id, f"<b>How many? (Price: {prices[item]} ETB each):</b>", reply_markup=markup)
    bot.register_next_step_handler(msg, process_pay, item, usage)

def process_pay(message, item, usage):
    if message.text == "🔙 Back": return main_menu(message)
    try:
        qty = int(message.text)
        total = qty * prices[item]
        
        banks_text = "<b>Payment Details:</b>\n\n"
        for b_id, b_info in bank_accounts.items():
            banks_text += f"🏦 {b_info['name']}\n👤 {b_info['owner']}\n🔢 <code>{b_info['acc']}</code> (Tap to copy)\n\n"
        
        banks_text += f"💰 <b>Total: {total} ETB</b>\n\nSend Screenshot + Location."
        bot.send_message(message.chat.id, banks_text, reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, final_submit, item, qty, total, usage)
    except: bot.send_message(message.chat.id, "❌ Enter a number!")

def final_submit(message, item, qty, total, usage):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ Please send a screenshot.")
        return
    
    u_id = message.from_user.id
    now = datetime.datetime.now()
    orders_db[u_id] = {"time": now, "total": total, "usage": usage, "assigned_to": None}

    caption = f"🔔 <b>New Order!</b>\n👤 {message.from_user.first_name}\n🆔 {u_id}\n📦 {item} x{qty}\n💰 {total} ETB\n🍽 {usage}\n📍 {message.caption}\n⏰ {now.strftime('%H:%M')}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Available ✅", callback_data=f"y_{u_id}_{total}"),
               types.InlineKeyboardButton("Not Available ❌", callback_data=f"n_{u_id}"))
    
    for admin in ADMIN_IDS:
        try: bot.send_photo(admin, message.photo[-1].file_id, caption=caption, reply_markup=markup)
        except: continue
    bot.send_message(u_id, "✅ <b>Sent! Waiting for admin confirmation...</b>")

# --- 6. ADMIN COMMANDS ---

@bot.message_handler(commands=['start_sales'])
def open_shop(message):
    if message.from_user.id not in ADMIN_IDS: return
    sales_status["is_open"] = True
    bot.send_message(message.chat.id, "✅ <b>Sales started.</b>")

@bot.message_handler(commands=['stop_sales'])
def close_shop(message):
    if message.from_user.id not in ADMIN_IDS: return
    msg = bot.send_message(message.chat.id, "<b>Why are you closing? (Reason):</b>")
    bot.register_next_step_handler(msg, save_stop_reason)

def save_stop_reason(message):
    sales_status["is_open"] = False
    sales_status["reason"] = message.text
    bot.send_message(message.chat.id, f"🚫 <b>Closed: {message.text}</b>")

@bot.message_handler(commands=['report'])
def get_report(message):
    if message.from_user.id not in ADMIN_IDS: return
    rep = f"📊 <b>Report</b>\n\n💰 Sales: {daily_report['total_sales']} ETB\n📦 Orders: {daily_report['orders_count']}"
    bot.send_message(message.chat.id, rep)

@bot.message_handler(commands=['to_user'])
def send_private(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        _, t_id, txt = message.text.split(" ", 2)
        bot.send_message(t_id, f"✉️ <b>Admin Message:</b>\n\n{txt}")
        bot.send_message(message.chat.id, "✅ Sent.")
    except: bot.send_message(message.chat.id, "Use: /to_user [ID] [Msg]")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id not in ADMIN_IDS: return
    txt = message.text.replace("/broadcast", "").strip()
    if not txt: return
    for u in all_users:
        try: bot.send_message(u, f"📢 <b>Announcement:</b>\n\n{txt}")
        except: continue
    bot.send_message(message.chat.id, "✅ Broadcast done.")

@bot.message_handler(commands=['set_price'])
def set_price(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        _, item, price = message.text.split()
        if item.lower() in prices:
            prices[item.lower()] = int(price)
            bot.send_message(message.chat.id, f"✅ {item} price set to {price}")
    except: bot.send_message(message.chat.id, "Use: /set_price [normal/special/super] [price]")

@bot.message_handler(commands=['add_bank'])
def add_bank(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        _, name, acc, owner = message.text.split(" ", 3)
        bank_accounts[name.lower()] = {"name": name, "acc": acc, "owner": owner}
        bot.send_message(message.chat.id, f"✅ Bank {name} added.")
    except: bot.send_message(message.chat.id, "Use: /add_bank [Name] [Acc] [Owner]")

@bot.message_handler(commands=['add_delivery'])
def add_delivery(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        d_id = int(message.text.split()[1])
        delivery_guys.append(d_id)
        bot.send_message(message.chat.id, "✅ Delivery guy added.")
    except: bot.send_message(message.chat.id, "Use: /add_delivery [ID]")

@bot.message_handler(commands=['add_channel'])
def add_channel(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        _, ch_id = message.text.split(" ", 1)
        if ch_id not in CHANNELS:
            CHANNELS.append(ch_id)
            bot.send_message(message.chat.id, f"✅ <b>{ch_id} successfully added to Welcome channels!</b>")
        else:
            bot.send_message(message.chat.id, "⚠️ <b>Channel already exists!</b>")
    except:
        bot.send_message(message.chat.id, "<b>Use:</b> <code>/add_channel @ChannelName</code>")

@bot.message_handler(commands=['remove_channel'])
def remove_channel(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        _, ch_id = message.text.split(" ", 1)
        if ch_id in CHANNELS:
            CHANNELS.remove(ch_id)
            bot.send_message(message.chat.id, f"🗑 <b>{ch_id} successfully removed!</b>")
        else:
            bot.send_message(message.chat.id, "⚠️ <b>Channel not found.</b>")
    except:
        bot.send_message(message.chat.id, "<b>Use:</b> <code>/remove_channel @ChannelName</code>")

@bot.message_handler(commands=['add_admin'])
def add_admin(message):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        _, new_admin_id = message.text.split(" ", 1)
        admin_id = int(new_admin_id)
        if admin_id not in ADMIN_IDS:
            ADMIN_IDS.append(admin_id)
            bot.send_message(message.chat.id, f"👑 <b>Admin (ID: {admin_id}) successfully added!</b>")
        else:
            bot.send_message(message.chat.id, "⚠️ <b>This user is already an admin.</b>")
    except:
        bot.send_message(message.chat.id, "<b>Use:</b> <code>/add_admin [ID]</code>")

# --- 7. CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_calls(call):
    data = call.data.split("_")
    now = datetime.datetime.now()

    if data[0] == "check_sub":
        if is_subscribed(call.from_user.id): 
            bot.answer_callback_query(call.id, "✅ Thank you for joining!")
            try: 
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except: 
                pass
            main_menu(call.message)
        else: 
            bot.answer_callback_query(call.id, "❌ You still haven't joined the channels!", show_alert=True)
            # አሁንም ያልተቀላቀለ ሰው ካለ በተኑ እንዳለ ሆኖ የቻናል መረጃውን እንዲያይ መልእክት እንልካለን
            markup = types.InlineKeyboardMarkup()
            for ch in CHANNELS:
                ch_name = ch.replace("@", "")
                btn = types.InlineKeyboardButton("Join Channel 📢", url=f"https://t.me/{ch_name}")
                markup.add(btn)
            check_btn = types.InlineKeyboardButton("Joined ✅", callback_data="check_sub")
            markup.add(check_btn)
            
            try:
                bot.send_message(call.message.chat.id, "❌ <b>You still haven't joined the required channel(s):</b>", reply_markup=markup)
            except:
                pass

    elif data[0] == "y":
        u_id, total = int(data[1]), int(data[2])
        daily_report["total_sales"] += total
        daily_report["orders_count"] += 1
        usage = orders_db[u_id]["usage"]
        
        if usage == "Dine-in":
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Received 👍", callback_data="finish"))
            bot.send_message(u_id, f"🎫 <b>Receipt</b>\n💰 Total: {total} ETB\n⏰ Time: {now.strftime('%H:%M')}\n\nShow this at the hotel.", reply_markup=markup)
        else:
            bot.send_message(u_id, "🥳 <b>Ertib is Ready! Finding delivery...</b>")
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚲 Accept", callback_data=f"t_{u_id}"))
            msg_ids = []
            for d in delivery_guys:
                try:
                    m = bot.send_message(d, f"🚚 <b>New Delivery!</b>\n{call.message.caption}", reply_markup=markup)
                    msg_ids.append((d, m.message_id))
                except: continue
            active_delivery_msgs[u_id] = msg_ids

    elif data[0] == "n":
        u_id = int(data[1])
        if u_id not in user_spam: user_spam[u_id] = [0, 0]
        user_spam[u_id][0] += 1
        user_spam[u_id][1] = time.time()
        bot.send_message(u_id, "❌ <b>Sorry, order rejected or sold out.</b>")
        for admin in ADMIN_IDS:
            try: bot.send_message(admin, f"⚠️ 'Not Available' sent to ID: <code>{u_id}</code>")
            except: continue

    elif data[0] == "t":
        u_id = int(data[1])
        if orders_db.get(u_id) and orders_db[u_id].get("assigned_to") is not None:
            bot.answer_callback_query(call.id, "❌ Already accepted!", show_alert=True)
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            return

        orders_db[u_id]["assigned_to"] = call.from_user.id
        if u_id in active_delivery_msgs:
            for d_id, m_id in active_delivery_msgs[u_id]:
                if d_id != call.from_user.id:
                    try: bot.delete_message(d_id, m_id)
                    except: pass
        
        bot.send_message(u_id, f"🛵 <b>Delivery {call.from_user.first_name} is on the way!</b>")
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Delivered ✅", callback_data=f"d_{u_id}"))
        bot.edit_message_text("✅ <b>You accepted this order.</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif data[0] == "d":
        u_id = data[1]
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Received 👍", callback_data="finish"))
        bot.send_message(u_id, "<b>Has it reached you?</b>", reply_markup=markup)
        bot.edit_message_text("🏁 <b>Marked delivered.</b>", call.message.chat.id, call.message.message_id)

    elif data[0] == "finish":
        u_id = call.from_user.id
        if u_id in orders_db and (now - orders_db[u_id]["time"]).total_seconds() < 43200:
            bot.edit_message_text("✅ <b>Completed!</b>", call.message.chat.id, call.message.message_id)
        else: bot.answer_callback_query(call.id, "Expired!", show_alert=True)

bot.polling(none_stop=True)

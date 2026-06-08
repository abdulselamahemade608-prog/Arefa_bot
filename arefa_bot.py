import os
import sqlite3
import re
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto

# --- 1. CONFIGURATION ---
API_ID = 36047636
API_HASH = "8389f0a19a5445af3afe72f85ae6f203"
BOT_TOKEN = "8572204621:AAEPpj978BOGAPK-3djHwEsV5421b-Gz0Zw"

SUPER_ADMIN = 7948454166  # ዋናው አድሚን (አንተ)

# የክፍል አድሚኖች መታወቂያ (ID)
ADMINS = {
    "9": 1614528462,
    "10": 7975950709,
    "11": 7948454166, # የ11 ክፍል ስላልተገለጸ ወደ አንተ ይላካል
    "12": 8192973594
}

app = Client("werabe_high_school_pro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 2. DATABASE SETUP ---
def init_db():
    # የድሮውን የሰንጠረዥ ስህተት ለማስተካከል ዳታቤዙን አዲስ ያደርገዋል
    if os.path.exists("school_pro.db"):
        os.remove("school_pro.db")
    conn = sqlite3.connect("school_pro.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (uid INTEGER PRIMARY KEY, name TEXT, age TEXT, gender TEXT, grade TEXT, 
                  photo_stu TEXT, photo_pay TEXT, photo_prev TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()
user_data = {}

# --- 3. REGISTRATION FLOW ---

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "እንኳን ወደ ወራቤ ሁለተኛ ደረጃ ትምህርት ቤት የምዝገባ ቦት በሰላም መጡ!\n\n"
        "ለመመዝገብ 'Register 📝' የሚለውን ይጫኑ።",
        reply_markup=ReplyKeyboardMarkup([["Register 📝"]], resize_keyboard=True)
    )

@app.on_message(filters.regex("Register 📝") & filters.private)
async def start_reg(client, message):
    user_data[message.from_user.id] = {"step": "name"}
    await message.reply_text("ሙሉ ስምዎን እስከ አያት (በእንግሊዘኛ ብቻ) ያስገቡ፦\n\nምሳሌ: Abdu Ahmed Mohammed", reply_markup=ReplyKeyboardRemove())

@app.on_message(filters.private & ~filters.command(["start", "list", "new", "All_admin_list"]))
async def handle_reg(client, message):
    uid = message.from_user.id
    if uid not in user_data: return
    step = user_data[uid].get("step")

    # 1. ስም (እንግሊዘኛ ብቻ እና 3 ቃላት)
    if step == "name":
        name = message.text
        if not re.match(r'^[a-zA-Z\s]+$', name) or len(name.split()) < 3:
            return await message.reply_text("❌ ስህተት! ስምዎን በእንግሊዘኛ ፊደላት ብቻ እና እስከ አያት (3 ቃላት) ያስገቡ።")
        user_data[uid]["name"] = name
        user_data[uid]["step"] = "age"
        await message.reply_text("እድሜዎን ያስገቡ፦")

    # 2. እድሜ
    elif step == "age":
        user_data[uid]["age"] = message.text
        user_data[uid]["step"] = "gender"
        await message.reply_text("ጾታ ይምረጡ፦", reply_markup=ReplyKeyboardMarkup([["Male", "Female"]], resize_keyboard=True))

    # 3. ጾታ
    elif step == "gender":
        user_data[uid]["gender"] = message.text
        user_data[uid]["step"] = "grade"
        await message.reply_text("ክፍል ይምረጡ፦", reply_markup=ReplyKeyboardMarkup([["9", "10", "11", "12"]], resize_keyboard=True))

    # 4. ክፍል
    elif step == "grade":
        user_data[uid]["grade"] = message.text
        user_data[uid]["step"] = "photo_stu"
        await message.reply_text("✅ አሁን የተማሪ **ጉርድ ፎቶ** ይላኩ፦", reply_markup=ReplyKeyboardRemove())

    # 5. ጉርድ ፎቶ
    elif step == "photo_stu":
        if message.photo:
            user_data[uid]["photo_stu"] = message.photo.file_id
            user_data[uid]["step"] = "photo_pay"
            await message.reply_text("✅ አሁን የከፈሉበትን **Screenshot** ይላኩ፦")
        else: await message.reply_text("እባክዎ ፎቶ ይላኩ!")

    # 6. የክፍያ ስክሪንሻት
    elif step == "photo_pay":
        if message.photo:
            user_data[uid]["photo_pay"] = message.photo.file_id
            user_data[uid]["step"] = "photo_prev"
            await message.reply_text("✅ በመጨረሻም የአምና **ማረጋገጫ ካርድ** ፎቶ ይላኩ፦")
        else: await message.reply_text("እባክዎ ፎቶ ይላኩ!")

    # 7. የአምና ካርድ
    elif step == "photo_prev":
        if message.photo:
            user_data[uid]["photo_prev"] = message.photo.file_id
            user_data[uid]["step"] = "final"
            await message.reply_text("📝 መረጃው ትክክል ከሆነ 'Submit ✅' ይጫኑ።",
                reply_markup=ReplyKeyboardMarkup([["Submit ✅", "Reset 🔄"]], resize_keyboard=True))
        else: await message.reply_text("እባክዎ ፎቶ ይላኩ!")

    # 8. መረጃውን ለአድሚን መላክ
    elif message.text == "Submit ✅" and user_data[uid]["step"] == "final":
        d = user_data[uid]
        target_admin = ADMINS.get(d['grade'], SUPER_ADMIN)
        
        media = [
            InputMediaPhoto(d["photo_stu"], caption=f"🔔 **አዲስ ተማሪ**\nስም: {d['name']}\nእድሜ: {d['age']}\nጾታ: {d['gender']}\nክፍል: {d['grade']}"),
            InputMediaPhoto(d["photo_pay"]),
            InputMediaPhoto(d["photo_prev"])
        ]
        
        await client.send_media_group(target_admin, media=media)
        await client.send_message(target_admin, f"የተማሪ {d['name']} ምዝገባ ይጽደቅ?", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Approve ✅", callback_data=f"ok_{uid}"), 
             InlineKeyboardButton("Reject ❌", callback_data=f"no_{uid}")]
        ]))
        await message.reply_text("✅ መረጃዎ ተልኳል፤ አድሚኑ እስኪያጸድቅ ይጠብቁ።", reply_markup=ReplyKeyboardRemove())

    elif message.text == "Reset 🔄":
        if uid in user_data: del user_data[uid]
        await message.reply_text("ተሰርዟል። ለመጀመር /start ይጫኑ።")

# --- 4. CALLBACKS (APPROVE/REJECT) ---
@app.on_callback_query()
async def callbacks(client, callback: CallbackQuery):
    action, target_uid = callback.data.split("_")
    target_uid = int(target_uid)
    
    if action == "ok":
        d = user_data.get(target_uid)
        if d:
            conn = sqlite3.connect("school_pro.db")
            conn.execute("INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?)",
                (target_uid, d['name'], d['age'], d['gender'], d['grade'], 
                 d['photo_stu'], d['photo_pay'], d['photo_prev'], "Approved"))
            conn.commit(); conn.close()
            await client.send_message(target_uid, "✅ እንኳን ደስ አለዎት! ምዝገባዎ በአድሚን ጸድቋል።")
            await callback.message.edit_text(f"✅ ተማሪ {d['name']} ጸድቋል።")
            del user_data[target_uid]
    
    elif action == "no":
        await client.send_message(target_uid, "❌ ይቅርታ፣ ምዝገባዎ ውድቅ ተደርጓል። እባክዎ መረጃዎን አስተካክለው እንደገና ይሞክሩ።")
        await callback.message.edit_text("❌ ምዝገባው ውድቅ ተደርጓል።")
        if target_uid in user_data: del user_data[target_uid]

# --- 5. ADMIN COMMANDS ---

@app.on_message(filters.command("list"))
async def list_students(client, message):
    aid = message.from_user.id
    if aid not in ADMINS.values() and aid != SUPER_ADMIN: return
    
    conn = sqlite3.connect("school_pro.db")
    rows = conn.execute("SELECT name, grade FROM students ORDER BY name ASC").fetchall()
    conn.close()
    
    if not rows: return await message.reply_text("📂 እስካሁን የጸደቀ ተማሪ የለም።")
    txt = "🎓 **የጸደቁ ተማሪዎች ዝርዝር (A-Z):**\n\n"
    for i, r in enumerate(rows, 1):
        txt += f"{i}. {r[0]} (Grade {r[1]})\n"
    await message.reply_text(txt)

@app.on_message(filters.command("All_admin_list") & filters.user(SUPER_ADMIN))
async def all_admin_list(client, message):
    conn = sqlite3.connect("school_pro.db")
    rows = conn.execute("SELECT name, grade FROM students ORDER BY grade ASC, name ASC").fetchall()
    conn.close()
    
    if not rows: return await message.reply_text("📂 ዝርዝሩ ባዶ ነው።")
    txt = "🎓 **አጠቃላይ የተማሪዎች ዝርዝር በየክፍሉ፦**\n"
    curr_grade = ""
    for name, grade in rows:
        if grade != curr_grade:
            txt += f"\n🔹 **Grade {grade}**\n"
            curr_grade = grade
        txt += f"  - {name}\n"
    await message.reply_text(txt)

@app.on_message(filters.command("new") & filters.user(SUPER_ADMIN))
async def broadcast(client, message):
    if len(message.command) < 2: return
    txt = message.text.split(None, 1)[1]
    conn = sqlite3.connect("school_pro.db")
    users = conn.execute("SELECT uid FROM students").fetchall()
    conn.close()
    for u in users:
        try: await client.send_message(u[0], f"📣 **መልዕክት ከአድሚን፦**\n\n{txt}")
        except: continue
    await message.reply_text("✅ መልዕክቱ ለሁሉም ተልኳል።")

print("Werabe Pro Bot is running...")
app.run()


import telebot
import sqlite3

# --- الإعدادات (تأكد من بياناتك) ---
TOKEN = '7859734337:AAGMzwP0l1sopff--p6deYxj_qEGopvmTZQ'
ADMIN_ID = 6113471878  # آيديك الخاص
CURRENCY = "دولار 💵"
bot = telebot.TeleBot(TOKEN)

# قائمة المتجر
STORE_ITEMS = {
    "تويوتا": 20000, "مرسيدس": 150000, "بوغاتي": 2000000,
    "شقة": 100000, "فيلا": 1000000, "قصر": 10000000,
    "طيارة": 150000000, "بنك": 1000000000, "جزيرة": 500000000
}

# --- إدارة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('mikey_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, money INTEGER, items TEXT, rank TEXT)''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('mikey_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT money, items, rank FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    if not res:
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (user_id, 1000, "", "مواطن"))
        conn.commit()
        res = (1000, "", "مواطن")
    conn.close()
    return {"money": res[0], "items": res[1].split(",") if res[1] else [], "rank": res[2]}

def update_db(user_id, money=None, items=None, rank=None):
    conn = sqlite3.connect('mikey_data.db', check_same_thread=False)
    c = conn.cursor()
    if money is not None: c.execute("UPDATE users SET money=? WHERE user_id=?", (money, user_id))
    if items is not None: c.execute("UPDATE users SET items=? WHERE user_id=?", (",".join(items), user_id))
    if rank is not None: c.execute("UPDATE users SET rank=? WHERE user_id=?", (rank, user_id))
    conn.commit()
    conn.close()

# --- أوامر المالك (بالرد) ---
@bot.message_handler(func=lambda m: m.reply_to_message is not None and m.from_user.id == ADMIN_ID)
def admin_reply_actions(message):
    target_id = message.reply_to_message.from_user.id
    target_name = message.reply_to_message.from_user.first_name
    text = message.text
    user = get_user(target_id)

    if text.startswith("اعطاء "):
        try:
            amt = int(text.split()[1])
            update_db(target_id, money=user['money'] + amt)
            bot.reply_to(message, f"✅ تم إعطاء {target_name} مبلغ {amt:,} {CURRENCY}")
        except: pass
    
    elif text.startswith("سحب "):
        try:
            amt = int(text.split()[1])
            update_db(target_id, money=max(0, user['money'] - amt))
            bot.reply_to(message, f"📉 تم سحب {amt:,} {CURRENCY} من {target_name}")
        except: pass

    elif text.startswith("رفع "):
        new_rank = text.replace("رفع ", "").strip()
        update_db(target_id, rank=new_rank)
        bot.reply_to(message, f"👑 تم رفع {target_name} لـ رتبة: {new_rank}")

    elif text == "تصفير":
        update_db(target_id, money=0, items=[], rank="مواطن")
        bot.reply_to(message, f"🎯 تم تصفير حساب {target_name} بالكامل!")

# --- أوامر القوة (لك فقط) ---
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "تفعيل القوة")
def god_mode(message):
    update_db(ADMIN_ID, money=999999999999999, items=list(STORE_ITEMS.keys()))
    bot.reply_to(message, "👑 وضع المالك: تم ضخ المليارات وتمليكك كل شيء!")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text.startswith("اعطيني "))
def give_self(message):
    try:
        amt = int(message.text.split()[1])
        u = get_user(ADMIN_ID)
        update_db(ADMIN_ID, money=u['money'] + amt)
        bot.reply_to(message, f"💰 تمت إضافة {amt:,} لرصيدك يا زعيم.")
    except: pass

# --- الأوامر العامة ---
@bot.message_handler(func=lambda m: m.text == "فلوسي")
def show_money(message):
    u = get_user(message.from_user.id)
    rank = "المالك الأسطوري 👑" if message.from_user.id == ADMIN_ID else u['rank']
    bot.reply_to(message, f"👤 الرتبة: {rank}\n💰 الرصيد: {u['money']:,} {CURRENCY}\n🆔 آيديك: `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "راتب")
def get_salary(message):
    u = get_user(message.from_user.id)
    update_db(message.from_user.id, money=u['money'] + 5000)
    bot.reply_to(message, f"✅ استلمت راتبك 5,000 {CURRENCY}")

@bot.message_handler(func=lambda m: m.text == "متجر")
def show_store(message):
    msg = "🛒 **متجر الفخامة:**\n"
    for k, v in STORE_ITEMS.items(): msg += f"🔹 {k}: {v:,} {CURRENCY}\n"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text.startswith("شراء "))
def buy_item(message):
    item = message.text.replace("شراء ", "").strip()
    if item in STORE_ITEMS:
        u = get_user(message.from_user.id)
        if u['money'] >= STORE_ITEMS[item]:
            u['items'].append(item)
            update_db(message.from_user.id, money=u['money'] - STORE_ITEMS[item], items=u['items'])
            bot.reply_to(message, f"✅ مبروك شراء {item}!")
        else: bot.reply_to(message, "❌ فلوسك ما تكفي!")

@bot.message_handler(func=lambda m: m.text == "ممتلكاتي")
def my_items(message):
    u = get_user(message.from_user.id)
    items_str = "\n".join(set([f"- {i} (x{u['items'].count(i)})" for i in u['items']])) if u['items'] else "لا يوجد"
    bot.reply_to(message, f"📦 **ممتلكاتك:**\n{items_str}", parse_mode="Markdown")

if __name__ == '__main__':
    init_db()
    print("🚀 البوت شغال الآن..")
    bot.infinity_polling()

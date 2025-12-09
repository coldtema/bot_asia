from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton




menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
menu.add("☎️Контакты", '📄Получить PDF-файл')



contacts = InlineKeyboardMarkup()
contacts.add(
    InlineKeyboardButton(text="Наш канал", url=f"https://t.me/Asia_Alliance")
)
contacts.add(
    InlineKeyboardButton(text="Менеджер", url=f"https://t.me/Asia_alliance_manager2")
)



markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
markup.add("✅ Пройти опрос", '⚠️ Напомнить позже')

for_whom = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
for_whom.add("🧍‍♂️ Для себя (физ. лицо)")
for_whom.add("🏢 Для компании / ИП")

budget_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
budget_menu.add("💸 До 2,5 млн ₽", "💰 2,5–4 млн ₽")
budget_menu.add("💼 4–6 млн ₽", "🏦 6+ млн ₽")

time_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
time_menu.add("⚡ В течение месяца", "⏳ 1–3 месяца")
time_menu.add("📆 3–6 месяцев", "🔍 Позже / просто изучаю")

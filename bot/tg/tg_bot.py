# bot/telegram_bot_telebot.py
import os
import django
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bot.settings")
django.setup()

from tg.models import User, SurveyAnswer
import telebot
from dotenv import load_dotenv
import logging
from telebot import TeleBot, types
import logging
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN') 
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID') 
CHANNEL_ID = os.getenv('CHANNEL_ID')
GROUP_ID = os.getenv('GROUP_ID')
if os.getenv('DEBUG'):
    PDF_PATH = 'Asia_Alliance.pdf'
else:
    PDF_PATH = '/root/bot_asia/Asia_Alliance.pdf'
bot = telebot.TeleBot(BOT_TOKEN)




bot = TeleBot(BOT_TOKEN)


def user_is_subscribed(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logging.error(f"Ошибка при проверке подписки: {e}")
        return False


def subscribe_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(text="✅ Подписаться на канал", url=f"https://t.me/Asia_Alliance")
    )
    keyboard.add(
        types.InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_subscription")
    )
    return keyboard




menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
menu.add("☎️Контакты", '📄Получить PDF-файл')



contacts = types.InlineKeyboardMarkup()
contacts.add(
    types.InlineKeyboardButton(text="Наш канал", url=f"https://t.me/Asia_Alliance")
)
contacts.add(
    types.InlineKeyboardButton(text="Менеджер", url=f"https://t.me/Asia_alliance_manager_Julia")
)



@bot.message_handler(commands=['start'])
def cmd_start(message: types.Message):
    user_id = message.from_user.id
    User.objects.get_or_create(telegram_id=user_id, defaults={'username': message.from_user.username or "..."})
    logging.info(f"Пользователь {user_id}")

    if user_is_subscribed(user_id):
        u = User.objects.filter(telegram_id=user_id).first()
        u.subscribed = True
        u.save()
        bot.send_message(user_id, "Отлично! Ты подписан ✅\nОтправляю PDF-файл 👇")
        try:
            bot.send_document(user_id, open(PDF_PATH, "rb"), caption="Вот твой файл 📄")
        except Exception as e:
            logging.error(f"Не удалось отправить PDF: {e}")
            bot.send_message(user_id, "Произошла ошибка при отправке PDF.")
    else:
        bot.send_message(
            user_id,
            "Чтобы получить доступ к материалу, подпишись на наш канал 👇",
            reply_markup=subscribe_keyboard()
        )


@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check_subscription(call: types.CallbackQuery):
    user_id = call.from_user.id
    logging.info(f"Пользователь {user_id}")

    if user_is_subscribed(user_id):
        u = User.objects.filter(telegram_id=user_id).first()
        u.subscribed = True
        u.save()
        bot.edit_message_text(
            "Подписка подтверждена ✅\nОтправляю PDF-файл 👇",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        try:
            bot.send_document(user_id, open(PDF_PATH, "rb"), caption="Вот твой файл 📄")
        except Exception as e:
            logging.error(f"Не удалось отправить PDF: {e}")
            bot.send_message(user_id, "Произошла ошибка при отправке PDF.")

        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(
            call.id,
            "Подписка не найдена. Убедись, что ты подписался и попробуй ещё раз.",
            show_alert=True
        )


@bot.callback_query_handler(func=lambda call: call.data.split('-')[0] == r"no_username")
def callback_check_subscription(call: types.CallbackQuery):
    user_id = call.data.split('-')[-1]
    bot.send_message(int(user_id), "У нашего менеджера уже готово подходящее решение для Вас!\nПожалуйста, свяжитесь с ним напрямую.\nВот его контакт: @Asia_alliance_manager_Julia")
    bot.edit_message_text(call.message.text + "\n\n⚠️ Пользователь не предоставил username. Отправлено сообщение для связи напрямую.", chat_id=call.message.chat.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == r"confirm_client")
def callback_check_subscription(call: types.CallbackQuery):
    bot.edit_message_text(call.message.text + "\n\n✅ Обработана", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    telegram_id = message.from_user.id
    User.objects.get_or_create(telegram_id=telegram_id, defaults={'username': message.from_user.username or "..."})
    state = User.objects.get(telegram_id=telegram_id).state

    if state == "ask_for_survey":
        return handle_ask_for_survey(message)
    
    elif state == "ask_time":
        return handle_ask_time(message)

    elif state == "ask_aim":
        return handle_ask_aim(message)

    elif state == "ask_budget_from":
        return handle_ask_budget_from(message)

    elif state == "ask_budget_to":
        return handle_ask_budget_to(message)
    
    elif message.text == '📄Получить PDF-файл':
        return cmd_start(message)
    
    elif message.text == '☎️Контакты':
        bot.send_message(telegram_id, "Наши контакты:", reply_markup=contacts)


    else:
        bot.send_message(telegram_id, "Выберите меню ниже:", reply_markup=menu)


def handle_ask_for_survey(message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    answer = message.text
    if answer == "✅Да":
         bot.send_message(telegram_id, "Отлично! Вопрос 1: В какое время рассматриваете покупку авто?", reply_markup=ReplyKeyboardRemove())
         user.state = "ask_time"
         user.save()
    elif answer == "⚠️Напомнить позже":
        bot.send_message(telegram_id, "Отзыв/информационный контент", reply_markup=menu)
        user.state = ""
        user.save()
    else:
        bot.send_message(telegram_id, "Пожалуйста, выберите вариант из клавиатуры.")


def handle_ask_time(message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    answer = message.text
    SurveyAnswer.objects.create(user=user, question="В какое время рассматриваете покупку авто?", answer=answer)
    bot.send_message(telegram_id, "Для каких целей планируете использовать авто?")
    user.state = "ask_aim"
    user.save()


def handle_ask_aim(message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    answer = message.text
    SurveyAnswer.objects.create(user=user, question="Для каких целей планируете использовать авто?", answer=answer)
    bot.send_message(telegram_id, "Введите бюджет от ... (в руб.)")
    user.state = "ask_budget_from"
    user.save()


def handle_ask_budget_from(message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    answer = message.text
    SurveyAnswer.objects.create(user=user, question="Введите бюджет от ... (в руб.)", answer=answer)
    bot.send_message(telegram_id, "Введите бюджет до ... (в руб.)")
    user.state = "ask_budget_to"
    user.save()

def handle_ask_budget_to(message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    answer = message.text
    SurveyAnswer.objects.create(user=user, question="Введите бюджет до ... (в руб.)", answer=answer)
    bot.send_message(telegram_id, "Связь с менеджером + подарок", reply_markup=menu)
    user.survey_passed = True
    user.state = ""
    user.save()
    # Отправка в админский чат
    answers = SurveyAnswer.objects.filter(user=user)
    answers_text = "\n\n".join([f"{a.question}: {a.answer}" for a in answers])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_client")
    )
    keyboard.add(
        types.InlineKeyboardButton(text="🔄 Нет Username", callback_data=f"no_username-{telegram_id}")
    )
    bot.send_message(ADMIN_CHAT_ID, f"Новый клиент: @{user.username}\n\n\n{answers_text}", reply_markup=keyboard)
    bot.send_message(GROUP_ID, f"Новый клиент: @{user.username}\n\n\n{answers_text}", reply_markup=keyboard)



if __name__ == "__main__":
    bot.infinity_polling()

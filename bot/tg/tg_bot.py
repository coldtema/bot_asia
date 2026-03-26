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
import keyboards
import messages

import telebot.apihelper as apihelper

load_dotenv()

apihelper.proxy = {
	'http': os.getenv('PROXY_URL'),
    'https': os.getenv('PROXY_URL'),
}

BOT_TOKEN = os.getenv('BOT_TOKEN') 
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID') 
CHANNEL_ID = os.getenv('CHANNEL_ID')
GROUP_ID = os.getenv('GROUP_ID')
if os.getenv('DEBUG'):
    PDF_PATH = 'Asia_Alliance.pdf'
    IMAGE_PATH = 'survey.png'
else:
    PDF_PATH = '/root/bot_asia/Asia_Alliance_160hp.pdf'
    IMAGE_PATH = '/root/bot_asia/survey.png'
bot = telebot.TeleBot(BOT_TOKEN)

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



@bot.message_handler(commands=['start'])
def cmd_start(message: types.Message):
    user_id = message.from_user.id
    User.objects.get_or_create(telegram_id=user_id, defaults={'username': message.from_user.username or "..."})
    logging.info(f"Пользователь {user_id}")

    if user_is_subscribed(user_id):
        u = User.objects.filter(telegram_id=user_id).first()
        u.state = ""
        u.subscribed = True
        u.save()
        bot.send_message(user_id, "Отлично! Ты подписан ✅\nОтправляю PDF-файл 👇")
        try:
            with open(PDF_PATH, "rb") as f:
                bot.send_document(
                    user_id,
                    f,
                    caption="Вот твой файл 📄",
                    reply_markup=keyboards.menu
                )
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
            bot.send_document(user_id, open(PDF_PATH, "rb"), caption="Вот твой файл 📄", reply_markup=keyboards.menu)
        except Exception as e:
            logging.error(f"Не удалось отправить PDF: {e}")
            bot.send_message(user_id, "Произошла ошибка при отправке PDF.", reply_markup=keyboards.menu)

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
    bot.send_message(
    int(user_id),
    "У нашего менеджера уже подготовлено подходящее решение для вас 💼\n\n"
    "<b>Пожалуйста, свяжитесь с ним напрямую.</b>\n\n"
    "Контакт: <b>@AsiaAllianceAvto</b>",
    parse_mode='HTML'
)
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
    
    elif state == "ask_for_whom":
        return handle_ask_for_whom(message)

    elif state == "ask_budget":
        return handle_ask_budget(message)

    elif state == "ask_time":
        return handle_ask_time(message)
    
    elif state == "ask_which":
        return handle_ask_which(message)
    
    elif message.text == '📄Получить PDF-файл':
        return cmd_start(message)
    
    elif message.text == '☎️Контакты':
        bot.send_message(telegram_id, "Наши контакты:", reply_markup=keyboards.contacts)


    else:
        bot.send_message(telegram_id, "Выберите меню ниже:", reply_markup=keyboards.menu)


def handle_ask_for_survey(message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    answer = message.text
    if answer == "✅ Пройти опрос":
         bot.send_message(telegram_id, "Отлично! <b>Для кого</b> планируешь привоз авто? 👥", reply_markup=keyboards.for_whom, parse_mode='HTML')
         user.state = "ask_for_whom"
         user.save()
    elif answer == "⚠️ Напомнить позже":
        bot.send_message(telegram_id, "Отзыв/информационный контент", reply_markup=keyboards.menu)
        user.state = ""
        user.save()
    else:
        bot.send_message(telegram_id, "Пожалуйста, выберите вариант из клавиатуры.")


def handle_ask_for_whom(message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    answer = message.text
    if answer == "🧍‍♂️ Для себя (физ. лицо)":
        bot.send_message(telegram_id, messages.for_whom_fiz)

    elif answer == "🏢 Для компании / ИП":
        bot.send_message(telegram_id, messages.for_whom_yur)

    else:
        bot.send_message(telegram_id, "Пожалуйста, выберите вариант из клавиатуры.")
        return
    
    SurveyAnswer.objects.create(user=user, question="👥 Для кого?", answer=answer)
    bot.send_message(telegram_id, "На какой <b>бюджет</b> ориентируешься за авто вместе с привозом из Кореи? 💰", reply_markup=keyboards.budget_menu, parse_mode='HTML')
    user.state = "ask_budget"
    user.save()


def handle_ask_budget(message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    answer = message.text

    if answer == "💸 До 2,5 млн ₽":
        bot.send_message(telegram_id, messages.budget_to_2_5)
    
    elif answer == "💰 2,5–4 млн ₽":
        bot.send_message(telegram_id, messages.budget_to_4)

    elif answer == "💼 4–6 млн ₽":
        bot.send_message(telegram_id, messages.budget_to_6)

    elif answer == "🏦 6+ млн ₽":
        bot.send_message(telegram_id, messages.budget_to_infinity)

    else:
        bot.send_message(telegram_id, "Пожалуйста, выберите вариант из клавиатуры.")
        return
    
    SurveyAnswer.objects.create(user=user, question="💰 Бюджет?", answer=answer)
    bot.send_message(telegram_id, "Когда примерно планируешь <b>покупку авто</b>? ⏳\n<i>Это нужно, чтобы корректно подобрать варианты и условия.</i>", reply_markup=keyboards.time_menu, parse_mode='HTML')
    user.state = "ask_time"
    user.save()


def handle_ask_time(message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    answer = message.text
    if answer in ['⚡ В течение месяца', '⏳ 1–3 месяца', '📆 3–6 месяцев', '🔍 Позже / просто изучаю']:
        SurveyAnswer.objects.create(user=user, question="⏳ Время?", answer=answer)
        bot.send_message(telegram_id, "Возможно, есть пожелания по <b>марке</b> или <b>модели</b> авто? 🚗", reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
        user.state = "ask_which"
        user.save()
    
    else:
        bot.send_message(telegram_id, "Пожалуйста, выберите вариант из клавиатуры.")
        return


def handle_ask_which(message):
    telegram_id = message.from_user.id
    user = User.objects.get(telegram_id=telegram_id)
    answer = message.text
    
    SurveyAnswer.objects.create(user=user, question="🚗 Марка/модель?", answer=answer)
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

    bot.send_photo(
            telegram_id,
            photo=open(IMAGE_PATH, 'rb'),
            caption=(
                "<b>Спасибо!</b> У меня уже сложилась картинка по твоему запросу по авто 🙌\n\n"
                "Как и обещали — за прохождение опроса ты получаешь <b>подарок на выбор</b>, "
                "который можно использовать при оформлении привоза авто из Кореи 🎁\n\n"
                "<i>Выбери, что тебе интереснее, и перешли это сообщение менеджеру:</i>\n"
                "<b>@AsiaAllianceAvto</b>"
            ),
            reply_markup=keyboards.menu,
            parse_mode='HTML'
        )



if __name__ == "__main__":
    bot.infinity_polling()

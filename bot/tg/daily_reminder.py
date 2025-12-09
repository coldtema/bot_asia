# bot/daily_reminder_telebot.py
import os
import django
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bot.settings")
django.setup()
from django.utils import timezone


from tg.models import User
import telebot
from telebot.types import ReplyKeyboardMarkup
import datetime
from tg_bot import bot
import time
from dotenv import load_dotenv
import keyboards
import messages

load_dotenv()


def remind_users():
    today = timezone.now()
    users = User.objects.filter(survey_passed=False)
    counter = 0
    for user in users:
        try:
            counter += 1
            if (today - user.created_at).days >= 0 and int(user.telegram_id) != int(os.getenv('ADMIN_CHAT_ID')):

                if not user.hello_message:
                    bot.send_message(user.telegram_id, messages.hello_message, reply_markup=keyboards.markup, parse_mode='HTML')
                    user.hello_message = True
                    user.save()
                else:
                    bot.send_message(user.telegram_id, messages.survey_message, reply_markup=keyboards.markup, parse_mode='HTML')
                user.state = 'ask_for_survey'
                user.save()
            if counter % 10 == 0:
                time.sleep(2)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user.telegram_id}: {e}")

if __name__ == "__main__":
    remind_users()

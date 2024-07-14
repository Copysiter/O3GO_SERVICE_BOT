import os, sys

import sqlite3
import time


from threading import Thread
from datetime import datetime, timedelta, timezone

import telebot
from telebot import types

from pony.orm import *
from db import *

from config import *

from scheduler import start_scheduler


bot = telebot.TeleBot(TELEBOT_BOT_TOKEN)


def reply_keyboard(user):
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row_width = 1
    markup_buttons = []
    if user.is_superuser:
        markup_buttons.append(types.KeyboardButton('👥 Пользователи'))
    markup.add(*markup_buttons)
    return markup


def user_info(user):
    return (f'User ID: {user.ext_id}\n' +
            f'Username: {user.username}\n' +
            f'First name: {user.first_name}\n' +
            f'Last name: {user.last_name}')


def user_keyboard(user):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            'Заблокировать' if user.is_active else 'Активировать',
            callback_data=f'USER:ACTIVATE:{user.id}'
        ),
        types.InlineKeyboardButton(
            'Удалить из базы', callback_data=f'USER:REMOVE:{user.id}'
        )
    )
    return markup


@bot.message_handler(commands=['start'])
def start_message(message):
    with db_session:
        user = User.get(lambda x: x.ext_id == message.from_user.id)
        if not user:
            user = User(
                ext_id = message.from_user.id,
                username = message.from_user.username,
                first_name = message.from_user.first_name,
                last_name = message.from_user.last_name,
                is_active = False,
                is_superuser = False
            )
            flush()
        name = [c for c in [user.first_name, user.last_name, user.username, user.ext_id] if c][0]
        if not user.is_active:
            text = f'💥 Приветствую Вас, <b>{name}</b>.\nВаш ID 622745113.\nДождитесь активации аккаунта.'
        else:
            text = f'💥 С возвращением, <b>{name}</b>.\nВаш ID 622745113.'
        bot.send_message(
            message.chat.id,
            text, parse_mode='HTML',
            reply_markup=(reply_keyboard(user) if user.is_active else False)
        )
        if not user.is_active:
            for superuser in User.select(lambda x: x.is_superuser)[:]:
                bot.send_message(
                    superuser.ext_id,
                    f'🔔 <b>Новый пользователь:</b>\n\n{user_info(user)}', parse_mode='HTML',
                    reply_markup=user_keyboard(user)
                )


@bot.message_handler(content_types='text')
def message_reply(message):
    with db_session:
        user = User.get(lambda x: x.ext_id == message.from_user.id)
        if user:

            if message.text == SUPER_USER_PSW:
                user.set(
                    is_active = True,
                    is_superuser = True
                )
                bot.send_message(
                    message.chat.id,
                    'Вы авторизоыаны в качестве администратора.', parse_mode='HTML',
                    reply_markup=reply_keyboard(user)
                )

            if user.is_active:

                if message.text == '👥 Пользователи':
                    if user.is_superuser:
                        for user in User.select(lambda x: x.id != user.id):
                            print(user.ext_id)
                            bot.send_message(
                                message.chat.id,
                                user_info(user), parse_mode='HTML',
                                reply_markup=user_keyboard(user)
                            )
            else:
                bot.send_message(message.chat.id, '🔒 Ваш аккаунт не активен')                


@bot.callback_query_handler(
    func=lambda call: call.data.startswith('USER')
)
def callback_user(call: types.CallbackQuery):
    action, user_id = call.data.split(':')[1:]
    with db_session:
        user = User.get(lambda x: x.id == user_id)
        print()
        print(user)
        print()
        if user:
            if action == 'ACTIVATE':
                if user.is_active:
                    user.set(
                        is_active=False
                    ) 
                    bot.send_message(
                        user.ext_id,
                        '🔒 Ваш аккаунт звблокирован',
                        parse_mode='HTML',
                        reply_markup=types.ReplyKeyboardRemove()
                    )
                    bot.edit_message_text(
                        chat_id = call.message.chat.id,
                        message_id = call.message.message_id,
                        text = '🔒 Пользователь звблокирован'
                    )
                else:
                    user.set(
                        is_active = True
                    ) 
                    bot.send_message(
                        user.ext_id,
                        '👍 Ваш аккаунт активирован',
                        parse_mode='HTML'
                    )
                    bot.edit_message_text(
                        chat_id = call.message.chat.id,
                        message_id = call.message.message_id,
                        text = '👍 Пользователь активирован'
                    )

            if action == 'REMOVE':
                user.delete()
                bot.send_message(
                    user.ext_id,
                    '🚫 Ваш аккаунт был удален', parse_mode='HTML',
                    reply_markup=types.ReplyKeyboardRemove()
                )
                bot.edit_message_text(
                    chat_id = call.message.chat.id,
                    message_id = call.message.message_id,
                    text = '🚫 Пользователь был удален'
                )


t = Thread(target=start_scheduler, args=(bot,), daemon=True)
t.start()
bot.infinity_polling()

# bot.polling()
# bot.register_next_step_handler(msg, answer)

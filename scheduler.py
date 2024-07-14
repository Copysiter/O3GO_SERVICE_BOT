import requests
import time
import prettytable as pt

from datetime import datetime, timedelta

from telebot import TeleBot

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger

from config import *

from pony.orm import *
from db import *


def start_scheduler(bot: TeleBot):
    def send_user_report():
        begin = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        end = begin - timedelta(hours=1)

        response = requests.get(
            O3GO_API_ADDR, params={
                # 'begin': begin.strftime('%Y-%m-%d %H:%M:%S'),
                # 'end': end.strftime('%Y-%m-%d %H:%M:%S')
                'begin': '2024-07-13 13:00:00',
                'end': '2024-07-13 17:00:00'
            }
        ).json()
        data = response['data']
        if len(data) > 0:
            messages = [f'<b>Критические отметки по регистрациям:</b>']
            for i, row in enumerate(data):
                left = f'StartCount: {row.get("start_count")}'
                right = f'CodeCount: {row.get("code_count")}'
                table = pt.PrettyTable([left, right])
                table.align[left] = 'l'
                table.align[right] = 'r'
                table.add_row(['ApiKey', row['api_key']])
                table.add_row(['DeviceID', row['device_ext_id']])
                table.add_row(['Service', row['service_name']])
                table.add_row(['StartCount', row['start_count']])
                table.add_row(['NumberCount', row['start_count']])
                table.add_row(['CodeCount', row['code_count']])
                messages.append(f'<pre>{table}</pre>')
            with db_session:
                for user in User.select(lambda x: x.is_active):
                    for message in messages:
                        bot.send_message(user.ext_id, message, parse_mode='HTML')

    scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})

    scheduler.add_job(
        send_user_report, trigger="cron", month="*", day="*",
        hour="*", minute="*/1"
    )

    scheduler.start()

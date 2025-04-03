import os
import requests
from time import sleep
from dotenv import load_dotenv
from telegram import Bot
import logging
from logging.handlers import RotatingFileHandler


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    load_dotenv()
    devman_token = os.environ['DEVMAN_TOKEN']
    tg_token = os.environ['TG_TOKEN']
    chat_id=os.environ['TG_CHAT_ID']
    bot = Bot(token=tg_token)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)

    rotating_handler = RotatingFileHandler(
        'app.log',
        maxBytes=20000,
        backupCount=2
    )
    rotating_handler.setFormatter(logging.Formatter('%(process)d %(levelname)s %(message)s'))
    logger.addHandler(rotating_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(process)d %(levelname)s %(message)s"))
    logger.addHandler(stream_handler)

    telegram_handler = TelegramLogsHandler(bot, chat_id)
    telegram_handler.setFormatter(logging.Formatter("%(process)d %(levelname)s %(message)s"))
    logger.addHandler(telegram_handler)

    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        "Authorization": f"Token {devman_token}"
    }

    timestamp = None

    while True:
        params = {}
        if timestamp:
            params['timestamp'] = timestamp

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            devman_response = response.json()

            if devman_response['status'] == 'found':
                timestamp = devman_response['last_attempt_timestamp']
            elif devman_response['status'] == 'timeout':
                timestamp = devman_response['timestamp_to_request']
            
            new_attempts = devman_response.get('new_attempts', [])
            if new_attempts:
                lesson_title = new_attempts[0]['lesson_title']
                lesson_url = new_attempts[0]['lesson_url']
                
                if new_attempts[0]['is_negative']:
                    text = f'Проверена работа "{lesson_title}".\n \nК сожалению, в работе нашлись ошибки.\n \nСсылка на урок: {lesson_url}'
                    bot.send_message(chat_id=chat_id, text=text)
                else:
                    text = f'Проверена работа "{lesson_title}".\n \nПреподавателю все понравилось, можно приступать к следующему уроку! .\n \nСсылка на урок: {lesson_url}'
                    bot.send_message(chat_id=chat_id, text=text)

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.Timeout:
            logger.error("Сервер не отвечает. Повторяем запрос...")
        except requests.exceptions.ConnectionError:
            logger.error('Проблема с подключением...')
            sleep(60)
        except requests.exceptions.RequestException as e:
            logger.exception('Произошла ошибка:', e)
            break


if __name__ == '__main__':
    main()
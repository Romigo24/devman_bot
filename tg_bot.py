import os
import requests
from dotenv import load_dotenv
from telegram import Bot


def main():
    load_dotenv()
    devman_token = os.getenv('DEVMAN_TOKEN')
    tg_token = os.getenv('TG_TOKEN')
    chat_id=os.getenv('TG_CHAT_ID')
    bot = Bot(token=tg_token)

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
            print(devman_response)

            if devman_response['status'] == 'found':
                timestamp = devman_response['last_attempt_timestamp']
            elif devman_response['status'] == 'timeout':
                timestamp = devman_response['timestamp_to_request']

            if devman_response['new_attempts'][0]['is_negative']:
                lesson_title = devman_response['new_attempts'][0]['lesson_title']
                lesson_url = devman_response['new_attempts'][0]['lesson_url']
                text = f'Проверена работа "{lesson_title}".\n \nК сожалению, в работе нашлись ошибки.\n \nСсылка на урок: {lesson_url}'
                bot.send_message(chat_id=chat_id, text=text)
            else:
                lesson_title = devman_response['new_attempts'][0]['lesson_title']
                lesson_url = devman_response['new_attempts'][0]['lesson_url']
                text = f'Проверена работа "{lesson_title}".\n \nПреподавателю все понравилось, можно приступать к следующему уроку! .\n \nСсылка на урок: {lesson_url}'
                bot.send_message(chat_id=chat_id, text=text)

        except requests.exceptions.Timeout:
            print("Сервер не отвечает. Повторяем запрос...")
        except requests.exceptions.ConnectionError:
            print('Проблема с подключением...')
        except requests.exceptions.RequestException as e:
            print('Произошла ошибка:', e)


if __name__ == '__main__':
    main()
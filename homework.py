import os
import logging
import time
import sys

import requests
import validators

from dotenv import load_dotenv
import telegram
from logging import StreamHandler
from http import HTTPStatus

from exception import URLNotResponding, URLNotValid

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)


def send_message(bot, message):
    """Отправляет сообщение пользователю."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(f'Сбой при отправке сообщения - {error}')


def get_api_answer(current_timestamp):
    """Получает ответ от эндпоинта."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    if requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=params
    ).status_code != HTTPStatus.OK:
        raise URLNotResponding(ENDPOINT)
    elif validators.url(ENDPOINT) is True:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        return response.json()
    else:
        raise URLNotValid(ENDPOINT)


def check_response(response):
    """Получает список всех домашних работ."""
    JsonKey = 'homeworks'
    if response is None:
        raise Exception(f'Нет данных в ответе - {response}')
    elif not isinstance(response, dict):
        raise TypeError
    else:
        homeworks = response.get(JsonKey)
        if homeworks is None:
            raise KeyError
        elif not isinstance(homeworks, list):
            raise AssertionError(f'Ответ по ключу {JsonKey} не в типе list.')
        return homeworks


def parse_status(homework):
    """Получает статус последней домашней работы."""
    JsonKey = 'homework_name'
    homework_name = homework.get(JsonKey)
    if homework_name is None:
        raise KeyError
    JsonKey = 'status'
    homework_status = homework.get(JsonKey)
    if homework_status is None:
        raise KeyError

    if homework_status in HOMEWORK_STATUSES.keys():
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        raise KeyError


def check_tokens():
    """Проверяет переменные окружения."""
    if PRACTICUM_TOKEN is None:
        logger.critical('Переменная окружения PRACTICUM_TOKEN отсутствует')
        return False
    if TELEGRAM_TOKEN is None:
        logger.critical('Переменная окружения TELEGRAM_TOKEN отсутствует')
        return False
    if TELEGRAM_CHAT_ID is None:
        logger.critical('Переменная окружения TELEGRAM_CHAT_ID отсутствует')
        return False
    return True


# flake8: noqa: C901
def main():
    """Основная логика работы бота."""
    CheckConstantsFlag = check_tokens()
    if CheckConstantsFlag is False:
        return

    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
    except Exception as error:
        logger.critical(f'Переменная TELEGRAM_TOKEN с ошибкой - {error}')
        return

    current_timestamp = int(time.time())
    ContinueFlag: bool = True

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if response.get('code') == 'not_authenticated':
                message = 'Учетные данные неверные (PRACTICUM_TOKEN)'
                logger.error(message)
                send_message(bot, message)
                return
            elif response.get('code') == 'UnknownError':
                message = 'Неверные ключи для доступа к эндпойнту'
                logger.error(message)
                send_message(bot, message)
                return
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
                send_message(bot, message)
                logger.info(f'Бот отправил сообщение - {message}')
            else:
                logger.debug('Отсутствие в ответе новых статусов')
            ContinueFlag = True

            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except URLNotValid as error:
            logger.error(error.message)
            if ContinueFlag is True:
                send_message(bot, error.message)
            ContinueFlag = False
            time.sleep(RETRY_TIME)

        except URLNotResponding as error:
            logger.error(error.message)
            if ContinueFlag is True:
                send_message(bot, error.message)
            ContinueFlag = False
            time.sleep(RETRY_TIME)

        except AssertionError:
            logger.error('Неверный тип данных')
            if ContinueFlag is True:
                send_message(bot, 'Неверный тип данных')
            ContinueFlag = False
            time.sleep(RETRY_TIME)

        except TypeError:
            logger.error('Неверный тип данных')
            if ContinueFlag is True:
                send_message(bot, 'Неверный тип данных')
            ContinueFlag = False
            time.sleep(RETRY_TIME)

        except KeyError:
            print(KeyError)
            logger.error('Ключ отсутсвует')
            if ContinueFlag is True:
                send_message(bot, 'Ключ отсутсвует')
            ContinueFlag = False
            time.sleep(RETRY_TIME)

        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            if ContinueFlag is True:
                send_message(bot, f'Сбой в работе программы: {error}')
            ContinueFlag = False
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == '__main__':
    main()

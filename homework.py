import os
import time
import sys
import logging
from logging import StreamHandler
from http import HTTPStatus

import requests
from dotenv import load_dotenv
import telegram
from json.decoder import JSONDecodeError

from exception import URLNotResponding, EmptyData


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
        logger.info(f'Бот отправил сообщение - {message}')
    except telegram.TelegramError as error:
        raise telegram.TelegramError(f'Не удалось отправить сообщение - {error}')


def get_api_answer(current_timestamp):
    """Получает ответ от эндпоинта."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise URLNotResponding(ENDPOINT)
        response = response.json()
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)
    except JSONDecodeError:
        raise JSONDecodeError('Ответ не преобразуется в json.')
    except ValueError as error:
        raise ValueError(f'Ответ не в формате json - {error}')
    except AttributeError as error:
        raise AttributeError(f'Ответ не имеет аттрибута json - {error}')
    else:
        return response


def check_response(response):
    """Получает список всех домашних работ."""
    json_key = 'homeworks'
    if response is None:
        raise EmptyData(response)
    elif not isinstance(response, dict):
        raise TypeError('Тип ответа не dict.')
    else:
        homeworks = response.get(json_key)
        if homeworks is None:
            raise KeyError(f'По ключу {json_key} нет данных.')
        elif not isinstance(homeworks, list):
            raise AssertionError(f'Ответ по ключу {json_key} не в типе list.')
        return homeworks


def parse_status(homework):
    """Получает статус последней домашней работы."""
    json_key = 'homework_name'
    homework_name = homework.get(json_key)
    if homework_name is None:
        raise KeyError(f'По ключу {json_key} нет данных.')
    json_key = 'status'
    homework_status = homework.get(json_key)
    if homework_status is None:
        raise KeyError(f'По ключу {json_key} нет данных.')
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        raise KeyError(f'По ключу {homework_status} нет данных.')


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
    check_constants_flag = check_tokens()
    if not check_constants_flag:
        return

    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
    except Exception as error:
        logger.critical(f'Переменная TELEGRAM_TOKEN с ошибкой - {error}')
        return

    current_timestamp = int(time.time())
    continue_flag: bool = True

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
                send_message(bot, message)
            else:
                logger.debug('Отсутствие в ответе новых статусов')
            continue_flag = True

            current_timestamp = int(time.time())

        except URLNotResponding as error:
            logger.error(error.message)
            if continue_flag:
                send_message(bot, error.message)
        
        except EmptyData as error:
            logger.error(error.message)
            if continue_flag:
                send_message(bot, error.message)

        except SystemExit as e:
            error = f'URL недоступно - {e.message}'
            logger.error(error)
            if continue_flag:
                send_message(bot, error)
        
        except JSONDecodeError as e:
            error = e.message
            logger.error(error)
            if continue_flag:
                send_message(bot, error)

        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            if continue_flag:
                send_message(bot, f'Сбой в работе программы: {error}')
        
        finally:
            time.sleep(RETRY_TIME)
            continue_flag = False


if __name__ == '__main__':
    main()

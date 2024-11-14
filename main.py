import logging
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import asyncio
import os
import tempfile

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Вставьте свой токен бота
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

SETTINGS_API = 'https://www.roblox.com/my/settings/json'

@dp.message(Command('start'))
async def start(message: types.Message):
    logging.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.reply("Привет! Отправь мне файл .txt с куками Roblox, и я проверю их для тебя.")

async def check_cookies(cookies_text: str):
    cookies_list = cookies_text.strip().splitlines()  # Разделяем куки по строкам
    results = []  # Список для хранения результатов проверки каждого куки

    for cookie in cookies_list:
        try:
            headers = {
                "Cookie": ".ROBLOSECURITY=" + cookie.strip(),
            }
            response = requests.get(SETTINGS_API, headers=headers)

            if response.status_code == 200 and "UserId" in response.text:
                main_info = response.json()
                user_id = main_info.get('UserId', None)
                email_verified = main_info.get('IsEmailVerified', False)

                ROBUX_API_URL = f'https://economy.roblox.com/v1/users/{user_id}/currency'
                robux_response = requests.get(ROBUX_API_URL, headers=headers)
                robux_balance = robux_response.json().get('robux', None)

                result_text = (
                    f"Информация о пользователе:\n"
                    f"UserID: {user_id}\n"
                    f"Баланс Robux: {robux_balance}\n"
                    f"Email подтвержден: {email_verified}\n"
                )
                logging.info(f"Успешная проверка для пользователя {user_id}: Баланс Robux: {robux_balance}")
            else:
                result_text = f"Ошибка проверки куки: {cookie}\n"
                logging.warning(f"Ошибка подключения к API Roblox для куки: {cookie}")
        except Exception as e:
            result_text = f"Произошла ошибка для куки {cookie}: {str(e)}\n"
            logging.error(f"Произошла ошибка для куки {cookie}: {str(e)}", exc_info=True)

        results.append(result_text)

    return "\n".join(results)

@dp.message(F.document)
async def check_cookies_txt(message: types.Message):
    document = message.document
    logging.info(f"Получен файл от пользователя {message.from_user.id}: {document.file_name}")

    if not document.file_name.endswith('.txt'):
        await message.reply("Ошибка: файл должен быть в формате .txt.")
        logging.warning(f"Файл от {message.from_user.id} не в формате .txt")
        return

    file_path = await bot.get_file(document.file_id)
    file = await bot.download_file(file_path.file_path)
    user_cookies_text = file.read().decode('utf-8')  # Чтение содержимого файла как текст

    logging.info(f"Файл куки успешно загружен от пользователя {message.from_user.id}")
    results = await check_cookies(user_cookies_text)

    # Сохраняем результаты во временный файл
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write(results)
        temp_file_path = temp_file.name

    # Отправляем результаты пользователю
    with open(temp_file_path, 'rb') as f:
        await message.reply_document(f)

    # Удаляем временный файл
    os.remove(temp_file_path)

@dp.message(F.text)
async def handle_message(message: types.Message):
    logging.info(f"Получено текстовое сообщение от {message.from_user.id}")
    await message.reply("Отправьте мне файл .txt с куками Roblox.")

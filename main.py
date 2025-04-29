import os

if not os.path.exists("htmls"):
    os.mkdir("htmls")
if not os.path.exists("db"):
    os.mkdir("db")

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import logging
import aiohttp
import db_function

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
BOT_TOKEN = "8058190209:AAGSkN4r1f7quq_T8PX2Ae49RIqrgSrMr5M"

dp = Dispatcher()
logger = logging.getLogger(__name__)


class Form(StatesGroup):  # создаем статусы, через которые будет проходить пользователь
    add_url = State()
    add_name = State()


async def user_verification(user: types.User):
    try:
        db_function.add_user(username=user.username)
    except Exception as e:
        if "уже существует" in str(e):
            pass


async def check_site(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200
    except Exception as e:
        return False


async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


def get_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="/add"),
                types.KeyboardButton(text="/list"),
            ],
            [
                types.KeyboardButton(text="/help"),
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


@dp.message(Command('start'))
async def process_start_command(message: types.Message):
    user = message.from_user
    try:
        await user_verification(user)
        await message.reply("<b>Бот для отслеживанию сайтов</b>\n\n"
                            "Этот бот поможет вам отслеживать изменения на ваших сайтах и уведомлять вас о них.\n\n"
                            "Доступные команды:\n"
                            "/add - Добавить новый сайт\n"
                            "/list - Список ваших сайтов\n"
                            "/delete - Удалить сайт\n"
                            "/history - Просмотреть историю изменений",
                            reply_markup=get_keyboard())
    except Exception as e:
        if "уже существует" in str(e):
            await message.answer(
                "Вы уже зарегистрированы!\n"
                "/add - Добавить новый сайт",
                reply_markup=get_keyboard()
            )
        else:
            logger.error(f"Error: {e}")
            await message.answer("Ошибка при регистрации")


@dp.message(Command('help'))
async def process_help_command(message: types.Message):
    await message.reply("<b>Справочная информация</b>\n\n"
                        "<b>Как использовать:</b>\n"
                        "1. Напишите /add для добавления нового сайта\n"
                        "2. Укажите интервал проверки (в минутах)\n"
                        "3. Опционально укажите CSS селектор для выбора конкретного элемента страницы\n\n"
                        "<b>Доступные команды:</b>\n"
                        "/add - Добавить новый сайт\n"
                        "/list - Список ваших сайтов\n"
                        "/delete - Удалить сайт\n"
                        "/history - Просмотреть историю изменений",
                        reply_markup=get_keyboard())


@dp.message(Command('add'))
async def process_add_command(message: types.Message, state: FSMContext):
    await user_verification(message.from_user)
    await state.set_state(Form.add_url)
    await message.answer("<b>Добавление нового сайта</b>\n\n"
                         "Пожалуйста, отправьте мне URL вашего сайта, который вы хотите отслеживать.\n"
                         "Например: <code>https://example.com</code>", reply_markup=ReplyKeyboardRemove())


@dp.message(Form.add_url)
async def process_url(message: types.Message, state: FSMContext):
    url = message.text.strip()
    if not (url.startswith("https://") or url.startswith("http://")):
        await message.answer("Введите корректный URL (начинается с http:// или https://)")
        return
    try:
        if not await check_site(url):
            await message.answer("Сайт недоступен. Попробуйте ещё раз.")
            return
        await state.update_data(url=url)
        await state.set_state(Form.add_name)
        await message.answer("Введите имя для сайта")

    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


@dp.message(Form.add_name)
async def site_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    data = await state.get_data()
    url = data.get("url")
    try:
        db_function.add_site(href=url, name=name, username=message.from_user.username)
        await message.answer("Сайт успешно добавлен!")
        await state.clear()
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        await state.clear()


if __name__ == '__main__':
    asyncio.run(main())

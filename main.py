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
from parse import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
BOT_TOKEN = "8058190209:AAGSkN4r1f7quq_T8PX2Ae49RIqrgSrMr5M"
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()
logger = logging.getLogger(__name__)


class Form(StatesGroup):  # создаем статусы, через которые будет проходить пользователь
    add_url = State()
    add_name = State()
    add_interval = State()
    delete_site = State()


async def send(user_id, message_text):
    try:
        chat = await bot.get_chat(user_id)
        if chat:
            await bot.send_message(user_id, message_text)
    except Exception as e:
        logger.error(f"Send error: {e}")


async def send_updates():
    while True:
        if recognition_stack:
            update = recognition_stack.pop(0)
            tg_id = update["user"].tg_id
            text = f"<b>Новые изменения на сайте {update['site'].name}:</b>\n\n{update['text']}\n\n{update['site'].href}"
            await send(tg_id, text)
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(10)


async def user_verification(user: types.User):
    try:
        db_function.add_user(username=user.username, tg_id=user.id)
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
    asyncio.create_task(check_all_site())
    asyncio.create_task(recognition_update())
    asyncio.create_task(send_updates())
    await dp.start_polling(bot)


def get_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="/add"),
                types.KeyboardButton(text="/list"),
            ],
            [
                types.KeyboardButton(text="/delete"),
                types.KeyboardButton(text="/history"),
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
                        "<b>Доступные команды:</b>\n"
                        "/add - Добавить новый сайт\n"
                        "/list - Список ваших сайтов\n"
                        "/delete - Удалить сайт\n"
                        "/history - Просмотреть историю изменений",
                        reply_markup=get_keyboard())


@dp.message(Command('list'))
async def process_list_command(message: types.Message):
    try:
        user = message.from_user
        sites = db_function.get_sites_username(user.username)
        if not sites:
            await message.answer("У вас нет отслеживаемых сайтов. Добавьте сайт командой /add",
                                 reply_markup=get_keyboard())
            return
        response = ["<b>Ваши отслеживаемые сайты:</b>\n"]
        for site in sites:
            response.append(f"\n<b>{site.name}</b>\n"
                            f"URL:  {site.href}\n")
        await message.answer("\n".join(response), reply_markup=get_keyboard())
    except Exception as e:
        logger.error(f"Error in /list {e}")
        await message.answer("Ошибка при получении списка сайтов", reply_markup=get_keyboard())


@dp.message(Command('delete'))
async def process_delete_command(message: types.Message, state: FSMContext):
    try:
        user = message.from_user
        sites = db_function.get_sites_username(user.username)

        if not sites:
            await message.answer("У вас нет сайтов для удаления", reply_markup=get_keyboard())
            return
        buttons = [
            [InlineKeyboardButton(text=site.name, callback_data=f"delete_{site.name}")]
            for site in sites
        ]

        await message.answer(
        "Выберите сайт для удаления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    except Exception as e:
        await message.answer(f"Ошибка: {e}", reply_markup=get_keyboard())


@dp.callback_query(lambda c: c.data.startswith('delete_'))
async def process_delete_callback(callback: types.CallbackQuery):
    try:
        site_name = callback.data[7:]
        username = callback.from_user.username
        db_function.delete_site(site_name, username)
        await callback.message.edit_text(f"Сайт '{site_name}' удалён")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in /delete {e}")
        await callback.message.answer("Ошибка при удалении сайта", reply_markup=get_keyboard())
        await callback.answer()


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
        await message.answer(f"Ошибка: {str(e)}", reply_markup=get_keyboard())


@dp.message(Form.add_name)
async def site_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    data = await state.get_data()
    url = data.get("url")
    username = message.from_user.username
    user_id = message.from_user.id
    try:
        db_function.add_site(href=url, name=name, username=username)
        await send(user_id, "Сайт успешно добавлен!")
        await message.answer("Сайт успешно добавлен!", reply_markup=get_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}", reply_markup=get_keyboard())
        await state.clear()


if __name__ == '__main__':
    asyncio.run(main())

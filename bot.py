from config import TG_TOKEN
import sqlite3
import json
from parsers import Funcs, sites
import asyncio
from datetime import datetime, time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import text
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
#cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    olympiads TEXT
)""")

conn.commit()
cursor.close()
conn.close()

API_TOKEN = TG_TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


async def send_info():
    while True:
        now = datetime.now().time()
        if now.minute % 5 == 0:
            print("send")
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            for i in range(len(Funcs)):
                print(sites[i])
                for news in Funcs[i]():
                    print(news)
                    for user in cursor.execute("SELECT user_id, olympiads FROM users").fetchall():
                        olympiads = json.loads(user[1])
                        user_id = user[0]
                        if sites[i] in olympiads:
                            await bot.send_message(chat_id=user_id, text=news)
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(30)


def make_keyboard():
    buttons = [
        [KeyboardButton(text="Добавить олимпиаду"), KeyboardButton(text="Удалить  олимпиаду")],
        [KeyboardButton(text="Посмотреть список моих олимпиад")],
        [KeyboardButton(text="Получить последние новости олимпиад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)




@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = make_keyboard()
    await message.answer("""Привет! Я — твой надежный помощник, который всегда подскажет, когда и где проходит следующая олимпиада. 🏆
С моей помощью ты сможешь:
✅ Настраивать уведомления о интересующих тебя олимпиадах.
✅ Быть в курсе всех важных событий и сроков.
✅ Получать информацию быстро и удобно.

Чтобы начать, воспользуйся кнопками ниже или введи команду /help, чтобы узнать больше о моих возможностях.
""", reply_markup=keyboard)

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        """✨ *Помощь по боту "Олимпиады"* ✨

Привет! Я — ваш надежный помощник в мире олимпиад и интеллектуальных состязаний. Вот что я могу сделать:

1. *Добавить олимпиаду*: Вы можете выбрать интересующие вас олимпиады из списка и получать уведомления о них.
2. *Удалить олимпиаду*: Если вам больше не интересна какая-то олимпиада, вы можете удалить её из вашего списка.
3. *Посмотреть список моих олимпиад*: Узнайте, какие олимпиады вы уже добавили, и проверьте актуальность информации.
4. *Получить последние новости олимпиад*: Будьте в курсе свежих новостей и обновлений по выбранным олимпиадам.

Если у вас есть дополнительные вопросы или нужна помощь, просто напишите мне, и я с радостью помогу!

Чтобы начать, воспользуйтесь кнопками ниже или введите команду снова.
""",
        parse_mode="Markdown"
    )



def generate_add_message(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    builder = InlineKeyboardBuilder()
    f = False
    for i in range(len(sites)):
        olympiads = cursor.execute("SELECT olympiads FROM users WHERE user_id = ?", (user_id,)).fetchall()
        if olympiads == [] or sites[i] not in json.loads(olympiads[0][0]):
            f = True
            builder.add(InlineKeyboardButton(text=sites[i],
                                             callback_data=f"add||{sites[i]}||{user_id}"))
            print(sites[i])
        builder.adjust(2)
    cursor.close()
    conn.close()
    if not f:
        return ("Все олимпиады уже добавлены",)
    else:
        return ("Выберите олимпиаду:", builder.as_markup())

def generate_delete_message(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    builder = InlineKeyboardBuilder()
    olympiads = cursor.execute("SELECT olympiads FROM users WHERE user_id = ?", (user_id,)).fetchall()
    if olympiads:
        olympiads = json.loads(olympiads[0][0])
    if olympiads == []:
        return ("У вас нет добавленных олимпиад",)
    else:
        for i in range(len(olympiads)):
            builder.add(InlineKeyboardButton(text=olympiads[i],
                                             callback_data=f"delete||{olympiads[i]}||{user_id}"))
        builder.adjust(2)
        return ("Выберите олимпиаду:", builder.as_markup())


@dp.message(lambda message: message.text == "Добавить олимпиаду")
async def add_olympiad(message: types.Message):
    args = generate_add_message(message.from_user.id)
    if len(args) == 2:
        await message.answer(args[0], reply_markup=args[1])
    else:
        await message.answer(args[0])


@dp.message(lambda message: message.text == "Удалить  олимпиаду")
async def delete_olympiad(message: types.Message):
    args = generate_delete_message(message.from_user.id)
    if len(args) == 2:
        await message.answer(args[0], reply_markup=args[1])
    else:
        await message.answer(args[0])

@dp.message(lambda message: message.text == "Посмотреть список моих олимпиад")
async def show_olympiads(message: types.Message):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    olympiads = cursor.execute("SELECT olympiads FROM users WHERE user_id = ?", (message.from_user.id,)).fetchall()
    if olympiads:
        olympiads = json.loads(olympiads[0][0])
    if olympiads == []:
        await message.answer("У вас нет добавленных олимпиад")
    else:
        s = ""
        for i in range(len(olympiads)):
            s += f"{i + 1}. {olympiads[i]}\n"
        await message.answer(f"""Ваши олимпиады:\n{s}""")
    cursor.close()
    conn.close()

@dp.message(lambda message: message.text == "Получить последние новости олимпиад")
async def get_news(message: types.Message):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    conn2 = sqlite3.connect("news.db")
    cursor2 = conn2.cursor()
    user_id = message.from_user.id
    olympiads = json.loads(cursor.execute("SELECT olympiads FROM users WHERE user_id = ?", (user_id,)).fetchall()[0][0])
    for olympiad in olympiads:
        news = json.loads(cursor2.execute("SELECT news FROM news WHERE title = ?", (olympiad,)).fetchall()[0][0])[-1]
        await message.answer(f"Новости олимпиады {olympiad}:\n{news}")
    cursor.close()
    conn.close()

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    type_action, site, user_id = callback.data.split("||")
    if type_action == "add":
        user_id = int(user_id)
        if user_id not in list(map(lambda x: x[0], cursor.execute("SELECT user_id FROM users").fetchall())):
            cursor.execute("INSERT INTO users (user_id, olympiads) VALUES (?, ?)", (user_id, json.dumps([])))
            conn.commit()
        olympiads = json.loads(cursor.execute("SELECT olympiads FROM users WHERE user_id = ?", (user_id,)).fetchall()[0][0])
        if site not in olympiads:
            olympiads.append(site)
            cursor.execute("UPDATE users SET olympiads = ? WHERE user_id = ?", (json.dumps(olympiads), user_id))
            conn.commit()
            await callback.message.answer(f"Олимпиада {site} успешно добавлена")
            args = generate_add_message(user_id)
            if len(args) == 2:
                await callback.message.edit_text(args[0], reply_markup=args[1])
            else:
                await callback.message.edit_text(args[0])
    elif type_action == "delete":
        user_id = int(user_id)
        olympiads = json.loads(cursor.execute("SELECT olympiads FROM users WHERE user_id = ?", (user_id,)).fetchall()[0][0])
        if site in olympiads:
            olympiads.remove(site)
            cursor.execute("UPDATE users SET olympiads = ? WHERE user_id = ?", (json.dumps(olympiads), user_id))
            conn.commit()
            await callback.message.answer(f"Олимпиада {site} успешно удалена")
            args = generate_delete_message(user_id)
            if len(args) == 2:
                await callback.message.edit_text(args[0], reply_markup=args[1])
            else:
                await callback.message.edit_text(args[0])
    conn.commit()
    cursor.close()
    conn.close()
    await callback.answer()


async def main():
    asyncio.create_task(send_info())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

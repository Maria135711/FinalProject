import asyncio
import logging
from db_function import *
import aiohttp
from config import *
from groq import Groq
from bs4 import BeautifulSoup

client = Groq(
    api_key=GROQ_API_KEY,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

stack = []


async def request(sys_instruction, user_input):
    success = False
    if type(user_input) == str:
        user_input = [user_input]
    messages = [
        {
            "role": "system",
            "content": f"""{sys_instruction}""".replace("\n", " ")
        },
    ] + [{"role": "user", "content": f"{i}",} for i in user_input]

    while not success:
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="deepseek-r1-distill-llama-70b",
            )
            success = True
            response = chat_completion.choices[0].message.content
            print(response)
            response = response.split("</think>")[1].strip()
            return response
        except Exception as e:
            logging.warning(f"Ошибка запроса: {e}")
            await asyncio.sleep(5)


async def answer_on_site_info(user, question):
    sites = get_sites_username(user.username)
    sites_texts = []
    for site in sites:
        with open(site.html, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            sites_texts.append(f"{site.name}: {soup.get_text(separator=' ', strip=True)}")
    sys_instruction = f"""Пользователь тебе отправляет тексты со всех сайтов, ты должен ответить на вопрос пользователя 
            основываясь на текстах сайтов, также при ответе ты должен упомянуть какие именно сайты были использованы"""
    response = await request(sys_instruction, sites_texts + [question])
    return response

async def check_all_site():
    while True:
        print("check")
        for user in get_all_users():
            sites = get_sites_username(user.username)
            for site in sites:
                with open(site.html, "r", encoding="utf-8") as f:
                    html_file_prev = f.read()
                response = requests.get(site.href)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                if soup.prettify() != html_file_prev:
                    stack.append({"user": user, "site": site, "html_new": soup.prettify()})
                    logging.info(f"Новые изменения на сайте '{site.name}' у пользователя '{user.username}'")
        await asyncio.sleep(300)


recognition_stack = []


async def recognition_update():
    while True:
        await asyncio.sleep(5)
        if stack:
            item = stack.pop(0)
            user = item["user"]
            site = item["site"]
            html_new = item["html_new"]
            soup = BeautifulSoup(html_new, 'html.parser')
            html_new = soup.get_text(separator=" ", strip=True)
            with open(site.html, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                html_file_prev = soup.get_text(separator=" ", strip=True)
            sys_instruction = f"""Тебе даётся два текста твоя задача показать что нового в тексте
                            второго текста не было в первом ты должен сформулировать текстом
                            ты должен описать только изменения не нужно писать "на второй странице изменилось ..." 
                            ты должен описать только изменения если существенные для пользователя изменений не найдено
                            то ты должен ответить чётко в так "НЕТ"""
            response = await request(sys_instruction, f"Первый: {html_file_prev}\nВторой: {html_new}")
            if response == "НЕТ":
                logging.info(f"Изменения на сайте '{site.name}' у пользователя '{user.username}' не распознаны")
            else:
                recognition_stack.append({"user": user, "site": site, "text": response})
                logging.info(f"Изменения на сайте '{site.name}' у пользователя '{user.username}' распознаны")
            with open(site.html, "w", encoding="utf-8") as f:
                f.write(html_new)


async def main():
    task1 = asyncio.create_task(check_all_site())
    task2 = asyncio.create_task(recognition_update())
    await task1  # Ждём завершения (если нужно)
    await task2  # Ждём завершения (если нужно)


if __name__ == "__main__":
    asyncio.run(main())

from google import genai
from google.genai import types as genai_types
import asyncio
import logging
from db_function import *
import aiohttp
from io import BytesIO

client = genai.Client(api_key="AIzaSyDiFFMzOKRCdMq4M11xHl2jHLZRGI-LgeA")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)


stack = []

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
                    logging.info(f"Новые изменения в сайте {site.name} у пользователя {user.username}")
        await asyncio.sleep(60)

recognition_stack = []

async def recognition_update():
    while True:
        await asyncio.sleep(5)
        if stack:
            item = stack.pop(0)
            user = item["user"]
            site = item["site"]
            html_new = item["html_new"]
            with open(site.html, "r", encoding="utf-8") as f:
                html_file_prev = f.read()
            while True:
                print("запрос")
                try:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[html_file_prev, html_new],
                        config=genai_types.GenerateContentConfig(
                            system_instruction="""Тебе даётся два html файла твоя задача показать что нового в тексте второго html файла не 
                            было в первом ты должен сформулировать текстом что изменилась нужно описывать изменение контента,
                            изменение структуры html описывать не нужно""",
                        )
                    )
                except Exception as e:
                    logging.warning(f"Ошибка при распознование изменений: {e}")
                finally:
                    break
            recognition_stack.append({"user": user, "site": site, "text": response.text})
            with open(site.html, "w", encoding="utf-8") as f:
                f.write(html_new)
            logging.info(f"Изменения в сайте {site.name} у пользователя {user.username} распознаны")


async def main():
    task1 = asyncio.create_task(check_all_site())
    task2 = asyncio.create_task(recognition_update())
    await task1  # Ждём завершения (если нужно)
    await task2  # Ждём завершения (если нужно)

if __name__ == "__main__":
    asyncio.run(main())

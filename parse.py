from google import genai
from google.genai import types
import asyncio
import logging
from db_function import *
import aiohttp
client = genai.Client(api_key="AIzaSyDiFFMzOKRCdMq4M11xHl2jHLZRGI-LgeA")

html_file_1 = client.files.upload(file="предпроф_NikitaCHistov_h4.html")
html_file_2 = client.files.upload(file="предпроф_NikitaCHistov_h5.html")




stack = []

async def check_all_site():
    while True:
        await asyncio.sleep(60)
        for user in get_all_users():
            sites = get_sites_username(user.username)
            for site in sites:
                with open(site.html, "w") as f:
                    html_file_prev = f.read()
                async with aiohttp.ClientSession() as session:
                    async with session.get(site.href) as response:
                        if response.text != html_file_prev:
                            stack.append({"user": user, "site": site, "html_new": response.text})
                            logging.info(f"Новые изменения в сайте {site.name} у пользователя {user.username}")


recognition_stack = []

async def recognition_update():
    while True:
        await asyncio.sleep(20)
        if stack:
            for i in stack:
                user = i["user"]
                site = i["site"]
                html_new = i["html_new"]
                with open(site.html, "w") as f:
                    html_file_prev = f.read()
                while True:
                    try:
                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=[html_file_prev, html_new],
                            config=types.GenerateContentConfig(
                                system_instruction="""Тебе даётся два html файла твоя задача показать что нового в тексте второго html файла не 
                                было в первом ты должен сформулировать текстом что изменилась нужно описывать изменение контента,
                                изменение структуры html описывать не нужно""",
                            )
                        )
                    except Exception as e:
                        logging.warning(f"Ошибка при распознование изменений: {e}")
                    finally:
                        break
                recognition_stack.append({"user": user, "site": site, "text": response.generations[0].content})



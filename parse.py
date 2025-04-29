from google import genai
from google.genai import types
client = genai.Client(api_key="AIzaSyDiFFMzOKRCdMq4M11xHl2jHLZRGI-LgeA")

html_file_1 = client.files.upload(file="предпроф_NikitaCHistov_h4.html")
html_file_2 = client.files.upload(file="предпроф_NikitaCHistov_h5.html")


response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[html_file_1, html_file_2],
    config=types.GenerateContentConfig(
        system_instruction="""Тебе даётся два html файла твоя задача показать что нового в тексте второго html файла не 
        было в первом ты должен сформулировать текстом что изменилась нужно описывать изменение контента,
        изменение структуры html описывать не нужно""",
    )
)
print(response.text)



async def check_site(user_id):
    pass
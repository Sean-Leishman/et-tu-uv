# from app2_maars import bot

# bot.infinity_polling()
from dotenv import dotenv_values
config = dotenv_values(".env")
TOKEN = config["b"]
print(config["b"])
import requests
TOKEN = config["b"]
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
print(requests.get(url).json())
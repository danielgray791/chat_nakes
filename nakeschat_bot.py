import asyncio
from typing import List, Callable
from handler import CommandHandler
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

class NakesChatBot: 
    def __init__(self):  
        self.bot = AsyncTeleBot(TOKEN)
        self.admin_bot = AsyncTeleBot(ADMIN_TOKEN)
      
    @classmethod
    async def init(cls): 
        cls_instance = cls()
        await cls_instance.bot.delete_webhook()
        await cls_instance.register_handler()
        return cls_instance

    async def register_handler(self): 
        CommandHandler(self.bot, self.admin_bot)
      
    async def run(self): 
        # Gunakan infinity_polling jika tersedia
        await self.bot.infinity_polling()

def monitor(environ, start_response):
    data = b"Hello, World!\n"
    start_response("200 OK", [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(data)))
    ])
    return iter([data])

async def main(): 
    try:
        nakeschat_bot = await NakesChatBot.init()
        await nakeschat_bot.run()
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__": 
    asyncio.run(main())

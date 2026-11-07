import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart

TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = "https://your-mini-app-url.com"  # Позже заменим на ссылку фронтенда

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_name = message.from_user.first_name
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📿 Тасбеҳни очиш / Открыть Тасбих", 
                    web_app=WebAppInfo(url=WEB_APP_URL)
                )
            ]
        ]
    )
    
    welcome_text = (
        f"Ассалому алайкум, <b>{user_name}</b>!\n\n"
        f"Бу тасбеҳ тапалка боти орқали сиз зикрлар қилиб, "
        f"шахсий ҳисобингизни юритишингиз мумкин.\n\n"
        f"Ўйинни бошлаш учун пастдаги тугмани босинг 👇"
    )
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")

async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен!")

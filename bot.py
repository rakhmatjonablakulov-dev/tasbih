import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Токен вашего бота (лучше хранить в Render в Environment Variables, но для теста можно и здесь)
TOKEN = "9078865133:AAEoI6LiCGLb2X-vs95b-qHAIAEx57VDquk"

# Ваша готовая ссылка на GitHub Pages
WEB_APP_URL = "https://rakhmatjonablakulov-dev.github.io/tasbih/"

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Создаем кнопку, которая открывает Web App (Мини-приложение)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📿 Тасбеҳни бошлаш", 
                    web_app=WebAppInfo(url=WEB_APP_URL)
                )
            ]
        ]
    )
    
    await message.answer(
        f"Ассалому алайкум, <b>{message.from_user.full_name}</b>!\n\n"
        "Бугунги зикрларингизни биз билан укинг. "
        "Қуйидаги тугмани босиб тасбеҳни очинг 👇",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def main() -> None:
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

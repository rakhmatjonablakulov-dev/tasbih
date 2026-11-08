import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Настройки бота
TOKEN = os.getenv("BOT_TOKEN", "9078865133:AAEoI6LiCGLb2X-vs95b-qHAIAEx57VDquk")
ADMIN_ID = 8274122612
WEBAPP_URL = "https://rakhmatjonablakulov-dev.github.io/tasbih/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Состояния для процесса вывода средств
class WithdrawStates(StatesGroup):
    waiting_for_details = State()

# Главное нижнее меню (5 пунктов с обновленными названиями)
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📿 Тасбеҳ")
    builder.button(text="💳 Пул чиқариш")
    builder.button(text="👥 Дўстларни таклиф қилиш")
    builder.button(text="📋 Вазифалар")
    builder.button(text="⭐ Рекламани кўриш")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    await message.answer(
        f"✨ Ассалому алайкум, <b>{user_name}</b>!\n\n"
        "Муборак Тасбеҳ ботига хуш келибсиз. 🌙",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

# 1. Кнопка "Тасбеҳ" (Запуск Mini App)
@dp.message(lambda msg: msg.text == "📿 Тасбеҳ")
async def open_tasbih(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Тасбеҳни очиш", web_app=types.WebAppInfo(url=WEBAPP_URL))
    
    await message.answer(
        "📿 Тасбеҳ мини-иловасини очиш учун қуйидаги тугмани босинг:",
        reply_markup=builder.as_markup()
    )

# 2. Кнопка "Пул чиқариш" — старт процесса
@dp.message(lambda msg: msg.text == "💳 Пул чиқариш")
async def process_withdrawal(message: types.Message, state: FSMContext):
    await message.answer(
        "💳 <b>Пул чиқариш сўрови</b>\n\n"
        "Ҳурматли фойдаланувчи! Тўплаган балларни курс бўйича ечиб олиш учун карта рақамингизни ёки тўлов тизимини юборинг.\n\n"
        "<i>(Масалан: 8600 1234 5678 9012 / Исм Шариф)</i>\n\n"
        "Бекор қилиш учун /cancel ни босинг.",
        parse_mode="HTML"
    )
    await state.set_state(WithdrawStates.waiting_for_details)

# Отмена операции вывода
@dp.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Амал бекор қилинди.", reply_markup=get_main_menu())

# Получение реквизитов от пользователя
@dp.message(WithdrawStates.waiting_for_details)
async def receive_withdrawal_details(message: types.Message, state: FSMContext):
    user = message.from_user
    details = message.text
    
    admin_text = (
        f"🔔 <b>Янги пул чиқариш сўрови! (Тасбеҳ)</b>\n\n"
        f"👤 Фойдаланувчи: @{user.username} (ID: <code>{user.id}</code>)\n"
        f"Исми: {user.first_name}\n"
        f"💳 Реквизит:\n<code>{details}</code>"
    )
    
    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Тўлаб берилди", callback_data=f"pay_yes_{user.id}")
        builder.button(text="❌ Рад этиш", callback_data=f"pay_no_{user.id}")
        builder.adjust(2)
        
        await bot.send_message(ADMIN_ID, admin_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
        await message.answer(
            "✅ <b>Сўровингиз қабул қилинди!</b>\n\n"
            "Администратор текширувидан кейин маблағ картангизга ўтказиб берилади. Сабр билан кутганингиз учун раҳмат!",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer("❌ Хатолик юз берди. Кейинроқ қайта уриниб кўринг.", reply_markup=get_main_menu())
    
    await state.clear()

# Обработка кнопок админа (Одобрить / Отклонить вывод)
@dp.callback_query(lambda c: c.data.startswith("pay_"))
async def admin_payment_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Сизда бунинг учун ҳуқуқ йўқ!", show_alert=True)
        return
    
    parts = callback.data.split("_")
    action, user_id = parts[1], int(parts[2])
    
    if action == "yes":
        await bot.send_message(user_id, "✅ Сизнинг пул чиқариш сўровингиз администратор томонидан тасдиқланди ва маблағ ўтказиб берилди! 🎉")
        await callback.message.edit_text(callback.message.text + "\n\n<b>✅ Статус: ТЎЛАНДИ</b>", parse_mode="HTML")
    else:
        await bot.send_message(user_id, "❌ Афсус, Сизнинг пул чиқариш сўровингиз рад этилди ёки маълумотлар нотўғри.")
        await callback.message.edit_text(callback.message.text + "\n\n<b>❌ Статус: РАД ЭТИЛДИ</b>", parse_mode="HTML")
        
    await callback.answer("Бажарилди!")

# 3. Кнопка "Дўстларни таклиф қилиш"
@dp.message(lambda msg: msg.text == "👥 Дўстларни таклиф қилиш")
async def process_referral(message: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    
    await message.answer(
        "👥 <b>Дўстларни таклиф қилиш</b>\n\n"
        "Дўстларингизни таклиф қилинг, биргаликда зикр қилинг ва умумий рейтингда юқори ўринларни эгалланг! (Бу тизим фақат дўстлар билан мусобақалашиш учун).\n\n"
        f"🔗 Сизнинг таклиф линкингиз:\n<code>{ref_link}</code>",
        parse_mode="HTML"
    )

# 4. Кнопка "Задания"
@dp.message(lambda msg: msg.text == "📋 Вазифалар")
async def process_tasks(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Спонсор каналга обуна бўлиш", callback_data="task_sub")
    builder.button(text="👀 Постни кўриш ва лайк босиш", callback_data="task_like")
    builder.adjust(1)
    
    await message.answer(
        "📋 <b>Кунлик вазифалар</b>\n\n"
        "Қуйидаги вазифаларни бажаринг ва қўшимча баллар қўлга киритинг:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# 5. Кнопка "Просмотр реклама"
@dp.message(lambda msg: msg.text == "⭐ Рекламани кўриш")
async def process_ads_view(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Рекламани кўриш ", web_app=types.WebAppInfo(url=WEBAPP_URL))
    
    await message.answer(
        "⭐ <b>Хайрли ишлар ва Реклама</b>\n\n"
        "Хайрли лойиҳаларни қўллаб-қувватлаш учун мини-иловадаги махсус тугма орқали рекламани кўришингиз мумкин. Эътиборингиз учун раҳмат!",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# --- АДМИН ПАНЕЛЬ ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Сизда админ ҳуқуқи йўқ.")
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="📢 Хабар юбориш (Рассылка)", callback_data="admin_broadcast")
    builder.adjust(1)
    
    await message.answer(
        "🛠 <b>Админ панелга хуш келибсиз!</b>\n\n"
        "Бошқариш учун керакли бўлимни танланг:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text(
        "📊 <b>Бот статистикаси:</b>\n\n"
        "• Жами фойдаланувчилар: <i>(Маълумотлар базаси улангандан кейин чиқади)</i>\n"
        "• Фаоллар бугун: <i>0</i>",
        parse_mode="HTML"
    )
    await callback.answer()

# Запуск бота
async def main():
    print("Тасбеҳ боти муваффақиятли ишга тушди...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

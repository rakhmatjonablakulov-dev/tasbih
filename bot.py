import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
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

# Муваққат базалар
users = set()                  
user_balances = {ADMIN_ID: 1000} # Мисол учун админга балл бериб турамиз
user_zikrs = {ADMIN_ID: 3000}    # Фойдаланувчиларнинг зикрлар сонини сақлаш учун база
user_names = {}                # Фойдаланувчи исмларини сақлаш учун

# Вазифалар базаси (id, title, reward, url)
tasks_list = [                 
    {"id": 1, "title": "📢 Расмий каналга обуна бўлиш", "reward": 50, "url": "https://t.me/telegram"},
    {"id": 2, "title": "⭐ Лойиҳани қўллаб-қувватлаш", "reward": 30, "url": "https://t.me/telegram"}
]

# Фойдаланувчилар бажарган вазифаларини сақлаш: {user_id: [task_id_1, task_id_2]}
user_completed_tasks = {}

# FSM Ҳолатлари
class WithdrawStates(StatesGroup):
    waiting_for_details = State()

class AdminBroadcast(StatesGroup):
    waiting_for_message = State()

class AdminBalance(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()

class AdminTask(StatesGroup):
    waiting_title = State()
    waiting_reward = State()
    waiting_url = State()


# 🌟 Энг чиройли ва замонавий асосий меню
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📿 Т А С Б Е Х Н И  О Ч И Ш")  
    builder.button(text="💳 Пулни ечиб олиш")
    builder.button(text="🏆 Рейтинг")
    builder.button(text="👥 Дўстларни таклиф")
    builder.button(text="📋 Вазифалар")
    builder.button(text="⭐ Рекламани кўриш")
    
    builder.adjust(1, 2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

# 🛠 Админ панелнинг чиройли менюси
def get_admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Статистика")
    builder.button(text="📢 Рассылка юбориш")
    builder.button(text="💰 Балансни бошқариш")
    builder.button(text="📋 Вазифа қўшиш")
    builder.button(text="⬅️ Асосий меню")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    users.add(user_id)
    user_names[user_id] = message.from_user.first_name or "Foydalanuvchi"
    
    if user_id not in user_balances:
        user_balances[user_id] = 0
    if user_id not in user_zikrs:
        user_zikrs[user_id] = 0

    user_name = message.from_user.first_name
    await message.answer(
        f"✨ Ассалому алайкум, <b>{user_name}</b>!\n\n"
        "🌙 <b>Муборак Тасбеҳ</b> расмий мини-илова ботига хуш келибсиз.\n\n"
        "<i>Аллоҳни зикр қилинг, қалбингиз ором олади. 👇</i>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

# Асосий менюга қайтиш
@dp.message(F.text == "⬅️ Асосий меню")
async def back_to_main_menu(message: types.Message):
    await message.answer("✨ Асосий менюга қайтдингиз.", reply_markup=get_main_menu())


# 1. Кнопка "Т А С Б Е Х Н И  О Ч И Ш"
@dp.message(lambda msg: msg.text == "📿 Т А С Б Е Х Н И  О Ч И Ш")
async def open_tasbih(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Мини-иловани ишга тушириш", web_app=types.WebAppInfo(url=WEBAPP_URL))
    
    await message.answer(
        "📿 <b>Т А С Б Е Х!</b>\n\n"
        "Қуйидаги тугма орқали интерактив мини-иловага ўтинг ва зикр қилишни бошланг:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


# 2. Кнопка "Пулни ечиб олиш"
@dp.message(lambda msg: msg.text == "💳 Пулни ечиб олиш")
async def process_withdrawal(message: types.Message, state: FSMContext):
    await message.answer(
        "💳 <b>Маблағни ечиб олиш маркази</b>\n\n"
        "Ҳурматли фойдаланувчи! ХОХЛОВЧИЛАР ЗИКР КИЛИБ ТУПЛАГАН БАЛЛАРИНИ НАХТ ПУЛ ШАКЛИДА ОЛИШЛАРИ МУМКИН .  Тўплаган балларни картага ёки тўлов тизимига ўтказиш учун реквизитларингизни юборинг.\n\n"
        "<i>(Масалан: 8600 1234 5678 9012 / Исм Шариф)</i>\n\n"
        "❌ Бекор қилиш учун /cancel ни босинг.",
        parse_mode="HTML"
    )
    await state.set_state(WithdrawStates.waiting_for_details)

@dp.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Жараён бекор қилинди.", reply_markup=get_main_menu())

@dp.message(WithdrawStates.waiting_for_details)
async def receive_withdrawal_details(message: types.Message, state: FSMContext):
    user = message.from_user
    details = message.text
    
    admin_text = (
        f"🔔 <b>Янги пул чиқариш сўрови!</b>\n\n"
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
            "Администратор текширувидан кейин маблағ картангизга ўтказиб берилади. Иштикорингиз учун раҳмат!",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    except Exception:
        await message.answer("❌ Хатолик юз берди. Кейинроқ қайта уриниб кўринг.", reply_markup=get_main_menu())
    
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith("pay_"))
async def admin_payment_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Сизда бунинг учун ҳуқуқ йўқ!", show_alert=True)
        return
    
    parts = callback.data.split("_")
    action, user_id = parts[1], int(parts[2])
    
    if action == "yes":
        await bot.send_message(user_id, "🎉 <b>Табриклаймиз!</b> Пул чиқариш сўровингиз тасдиқланди ва маблағ картангизга ўтказилди!")
        await callback.message.edit_text(callback.message.text + "\n\n<b>✅ Статус: ТЎЛАНДИ ВА ЯКУНланДИ</b>", parse_mode="HTML")
    else:
        await bot.send_message(user_id, "❌ Афсус, сўровингиз маълумотлар хатолиги ёки бошқа сабабга кўра рад этилди.")
        await callback.message.edit_text(callback.message.text + "\n\n<b>❌ Статус: РАД ЭТИЛДИ</b>", parse_mode="HTML")
        
    await callback.answer("Бажарилди!")


# 🏆 РЕЙТИНГ ТУГМАСИ (ЗИКРЛАР СОНИ БИЛАН ЯНГИЛАНГАН)
@dp.message(lambda msg: msg.text == "🏆 Рейтинг")
async def show_leaderboard(message: types.Message):
    # Рейтингни баллар бўйича саралаймиз (ёки хоҳласангиз user_zikrs бўйича ҳам саралаш мумкин)
    sorted_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)[:10]
    
    text = (
        "🏆 <b>Энг фаол зикр қилувчилар рейтинги (Топ-10)</b>\n\n"
        "💡 <b>Баллар ва зикрлар нима учун берилади?</b>\n"
        "• Мини-иловада зикр қилганингизда;\n"
        "• Кунлик вазифаларни бажарганингизда;\n"
        "• Рекламаларни кўриб лойиҳани қўллаб-қувватлаганингизда балансингизга баллар қўшилиб боради!\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🏅 <b>Пешқадамлар рўйхати:</b>\n\n"
    )
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for index, (uid, balance) in enumerate(sorted_users):
        name = user_names.get(uid, f"Фойдаланувчи {uid}")
        medal = medals[index] if index < len(medals) else f"{index+1}."
        
        # Ҳар бир фойдаланувчининг аниқ зикрлар сонини оламиз (агар бўлмаса балансга қараб ҳисоблаймиз ёки базадан оламиз)
        zikr_count = user_zikrs.get(uid, balance * 5) # Мисол учун ҳар 1 балл 5 та зикрга тенг ёки тўғридан-тўғри олинади
        
        text += f"{medal} <b>{name}</b>\n    └ 📿 Зикрлар: <b>{zikr_count:,} та</b> | 💎 Баллар: <b>{balance}</b>\n\n"
        
    text += "<i>✨ Қанча кўп зикр қилсангиз, рейтинг юқорисига чиқасиз!</i>"
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())


# 3. Кнопка "Дўстларни таклиф"
@dp.message(lambda msg: msg.text == "👥 Дўстларни таклиф")
async def process_referral(message: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    
    await message.answer(
        "👥 <b>Дўстларни таклиф қилиш тизими</b>\n\n"
        "Яқинларингизни таклиф қилинг, савобга шерик бўлинг ва биргаликда рейтингда пешқадам бўлинг!\n\n"
        f"🔗 <b>Сизнинг шахсий линкингиз:</b>\n<code>{ref_link}</code>",
        parse_mode="HTML"
    )


# 4. Кнопка "Вазифалар"
@dp.message(lambda msg: msg.text == "📋 Вазифалар")
async def process_tasks(message: types.Message):
    if not tasks_list:
        await message.answer("📋 Ҳозирча янги вазифалар мавжуд эмас.", reply_markup=get_main_menu())
        return
    
    user_id = message.from_user.id
    completed = user_completed_tasks.get(user_id, [])
    
    await message.answer("📋 <b>Кунлик вазифалар ва бонуслар</b>\n\nҚуйидаги вазифаларни бажариб баллар жамғаринг:", parse_mode="HTML")
    
    for task in tasks_list:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔗 Бажариш", url=task['url'])
        
        if task['id'] in completed:
            builder.button(text="✅ Бажарилган", callback_data=f"noop_{task['id']}")
        else:
            builder.button(text="🎁 Текшириш ва олиш", callback_data=f"check_task_{task['id']}")
            
        builder.adjust(2)
        
        await message.answer(
            f"📌 <b>{task['title']}</b>\n🎁 Мукофот: <b>+{task['reward']} балл</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

# Вазифани текшириш ва балл бериш callback
@dp.callback_query(lambda c: c.data.startswith("check_task_") or c.data.startswith("noop_"))
async def task_callback_handler(callback: types.CallbackQuery):
    if callback.data.startswith("noop_"):
        await callback.answer("Сиз бу вазифани аллақачон бажаргансиз!", show_alert=True)
        return
        
    task_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    target_task = next((t for t in tasks_list if t['id'] == task_id), None)
    if not target_task:
        await callback.answer("Вазифа топиilmadi!", show_alert=True)
        return
        
    if user_id not in user_completed_tasks:
        user_completed_tasks[user_id] = []
        
    if task_id in user_completed_tasks[user_id]:
        await callback.answer("Сиз бу вазифа учун аллақачон балл олгансиз!", show_alert=True)
        return
        
    user_completed_tasks[user_id].append(task_id)
    if user_id not in user_balances:
        user_balances[user_id] = 0
        
    user_balances[user_id] += target_task['reward']
    
    # Шунингдек, вазифа учун ҳам мукофот тариқасида зикрлар сонини қўшиб қўямиз (масалан, баллар * 10 миқдорида)
    if user_id not in user_zikrs:
        user_zikrs[user_id] = 0
    user_zikrs[user_id] += target_task['reward'] * 10
    
    await callback.answer(f"🎉 Табриклаймиз! +{target_task['reward']} балл қўшилди.", show_alert=True)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Бажариш", url=target_task['url'])
    builder.button(text="✅ Бажарилган", callback_data=f"noop_{task_id}")
    builder.adjust(2)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except Exception:
        pass


# 5. Кнопка "Рекламани кўриш"
@dp.message(lambda msg: msg.text == "⭐ Рекламани кўриш")
async def process_ads_view(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Рекламани кўриш ва қўллаб-қувватлаш", web_app=types.WebAppInfo(url=WEBAPP_URL))
    
    await message.answer(
        "⭐ <b>Хайрли ишларни қўллаб-қувватланг</b>\n\n"
        "Рекламани кўриш орқали лойиҳамизни ривожлантиришга ўз ҳиссангизни қўшинг. Эътиборингиз учун раҳмат!",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


# ==========================================
# ------------ АДМИН ПАНЕЛЬ КОДИ ------------
# ==========================================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Сизда бу буйруқни ишлатиш ҳуқуқи йўқ.")
        return
        
    await message.answer(
        "🛠 <b>Бошқарув панели (Админ)</b>\n\n"
        "Қуйидаги тугмалардан керакли бўлимни танланг:",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )

@dp.message(F.text == "📊 Статистика")
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        f"📊 <b>Тизим статистикаси:</b>\n\n"
        f"• Жами фойдаланувчилар: <b>{len(users)} та</b>",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )

@dp.message(F.text == "📢 Рассылка юбориш")
async def admin_broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminBroadcast.waiting_for_message)
    await message.answer(
        "📢 Барча фойдаланувчиларга юбормоқчи бўлган хабарингизни (матн, расм ёки видео) юборинг:\n\n"
        "<i>Бекор қилиш учун 'отмена' денг.</i>",
        parse_mode="HTML"
    )

@dp.message(AdminBroadcast.waiting_for_message)
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
        
    if message.text and message.text.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Рассылка бекор қилинди.", reply_markup=get_admin_menu())
        return
        
    await state.clear()
    await message.answer("🚀 Рассылка юбориш жараёни бошланди...")
    
    success = 0
    failed = 0
    for uid in list(users):
        try:
            await message.copy_to(chat_id=uid)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
            
    await message.answer(
        f"✅ <b>Рассылка муваффақиятли якунланди!</b>\n\n"
        f"🟢 Етиб борди: <b>{success} та</b>\n"
        f"🔴 Блок қилганлар: <b>{failed} та</b>",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )

@dp.message(F.text == "💰 Балансни бошқариш")
async def admin_balance_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminBalance.waiting_user_id)
    await message.answer("🆔 Балансини ўзгартирмоқчи бўлган фойдаланувчининг <b>Telegram ID</b> сини киритинг:", parse_mode="HTML")

@dp.message(AdminBalance.waiting_user_id)
async def admin_balance_get_id(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text)
        await state.update_data(target_id=target_id)
        await state.set_state(AdminBalance.waiting_amount)
        await message.answer(f"✍️ Фойдаланувчи (ID: {target_id}) учун қўшиладиган ёки айриладиган балл миқдорини киритинг (Масалан: `100` ёки `-50`):")
    except ValueError:
        await message.answer("❌ Фақат рақамлардан иборат ID киритинг:")

@dp.message(AdminBalance.waiting_amount)
async def admin_balance_get_amount(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        amount = int(message.text)
        data = await state.get_data()
        target_id = data.get("target_id")
        
        if target_id not in user_balances:
            user_balances[target_id] = 0
            
        user_balances[target_id] += amount
        await state.clear()
        
        await message.answer(
            f"✅ Муваффақиятли! Фойдаланувчининг янги баланси: <b>{user_balances[target_id]} балл</b>",
            parse_mode="HTML",
            reply_markup=get_admin_menu()
        )
        
        try:
            await bot.send_message(target_id, f"🎁 Админ томонидан балансингиз ўзгартирилди! Жорий баланс: {user_balances[target_id]} балл")
        except Exception:
            pass
            
    except ValueError:
        await message.answer("❌ Фақат бутун рақам киритинг (масалан: 50 ёки -20):")


# --- Админ орқали янги вазифа қўшиш ---
@dp.message(F.text == "📋 Вазифа қўшиш")
async def admin_task_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminTask.waiting_title)
    await message.answer("✍️ Янги вазифа номини ва шартини киритинг (Масалан: `📢 Телеграм каналга обуна бўлиш`):")

@dp.message(AdminTask.waiting_title)
async def admin_task_get_title(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(title=message.text)
    await state.set_state(AdminTask.waiting_reward)
    await message.answer("💰 Ушбу вазифа учун бериладиган мукофот (балл) миқдорини рақамда киритинг (Масалан: `50`):")

@dp.message(AdminTask.waiting_reward)
async def admin_task_get_reward(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        reward = int(message.text)
        await state.update_data(reward=reward)
        await state.set_state(AdminTask.waiting_url)
        await message.answer("🔗 Вазифа учун ҳаволани (URL ёки t.me манзилини) киритинг:")
    except ValueError:
        await message.answer("❌ Фақат рақам киритинг (масалан: 50):")

@dp.message(AdminTask.waiting_url)
async def admin_task_get_url(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    url = message.text.strip()
    data = await state.get_data()
    title = data.get("title")
    reward = data.get("reward")
    
    new_id = len(tasks_list) + 1
    tasks_list.append({"id": new_id, "title": title, "reward": reward, "url": url})
    await state.clear()
    
    await message.answer(
        f"✅ <b>Янги вазифа муваффақиятли қўшилди!</b>\n\n📌 Номи: {title}\n🎁 Мукофот: {reward} балл\n🔗 Ҳавола: {url}",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )


# Запуск бота
async def main():
    print("Тасбеҳ боти муваффақиятли ишга тушди...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

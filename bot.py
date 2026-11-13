import os
import asyncio
import json
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Настройки бота (Токенни @BotFather орқали янгилаб, шу ерга ёки муҳит ўзгарувчисига қўйинг)
TOKEN = os.getenv("BOT_TOKEN", "ЯНГИ_ТОКЕННИ_ШУ_ЕРГА_ҚЎЙИНГ")
ADMIN_ID = 8274122612
WEBAPP_URL = "https://rakhmatjonablakulov-dev.github.io/tasbih/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

TASKS_FILE = "tasks.json"
USERS_FILE = "users_data.json"

# --- МАЪЛУМОТЛАРНИ САҚЛАШ ВА ЎҚИШ ---
def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
                current_time = time.time()
                
                # Муддати ўтмаган вазифаларни қолдирамиз (expires_at мавжуд ва вақти ўтган бўлса ташлаймиз)
                active_tasks = []
                for task in tasks:
                    expires_at = task.get('expires_at')
                    # Агар expires_at None бўлса — бу чексиз вазифа дегани
                    if expires_at is None or expires_at > current_time:
                        active_tasks.append(task)
                
                # Агар муддати ўтган вазифалар ўчирилган бўлса, файлни янгилаб қўямиз
                if len(active_tasks) != len(tasks):
                    save_tasks(active_tasks)
                    
                return active_tasks
        except Exception:
            pass
            
    # Бошланғич вазифалар (чексиз муддат билан)
    return [                 
        {"id": 1, "title": "📢 Расмий каналга обуна бўлиш", "reward": 50, "url": "https://t.me/telegram", "expires_at": None},
        {"id": 2, "title": "⭐ Лойиҳани қўллаб-қувватлаш", "reward": 30, "url": "https://t.me/telegram", "expires_at": None}
    ]

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def delete_task_by_id(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t['id'] != task_id]
    save_tasks(tasks)
    return tasks

def load_users_data():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # JSON калитларини int га ўтказиш
                return {
                    "users": set(data.get("users", [])),
                    "balances": {int(k): v for k, v in data.get("balances", {}).items()},
                    "names": {int(k): v for k, v in data.get("names", {}).items()},
                    "referred": set(data.get("referred", [])),
                    "completed_tasks": {int(k): v for k, v in data.get("completed_tasks", {}).items()}
                }
        except Exception:
            pass
    return {
        "users": {ADMIN_ID},
        "balances": {ADMIN_ID: 1000},
        "names": {ADMIN_ID: "Admin"},
        "referred": set(),
        "completed_tasks": {}
    }

def save_users_data():
    data = {
        "users": list(users),
        "balances": user_balances,
        "names": user_names,
        "referred": list(referred_users),
        "completed_tasks": user_completed_tasks
    }
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Базани юклаш
tasks_list = load_tasks()
db_data = load_users_data()
users = db_data["users"]
user_balances = db_data["balances"]
user_names = db_data["names"]
referred_users = db_data["referred"]
user_completed_tasks = db_data["completed_tasks"]

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
    waiting_hours = State()

# Асосий меню
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📿 Т А С Б Е Х Н И  О Ч И Ш")
    builder.button(text="💰 Балансим")
    builder.button(text="💳 Пулни ечиб олиш")
    builder.button(text="🏆 Рейтинг")
    builder.button(text="👥 Дўстларни таклиф")
    builder.button(text="📋 Вазифалар")
    builder.button(text="⭐ Рекламани кўриш")
    builder.adjust(1, 2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

# Админ панел менюси
def get_admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Статистика")
    builder.button(text="👥 Фойдаланувчилар")
    builder.button(text="📢 Рассылка юбориш")
    builder.button(text="💰 Балансни бошқариш")
    builder.button(text="📋 Вазифа қўшиш")
    builder.button(text="📋 Вазифаларни бошқариш")
    builder.button(text="⬅️ Асосий меню")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    users.add(user_id)
    user_names[user_id] = message.from_user.first_name or "Foydalanuvchi"

    if user_id not in user_balances:
        user_balances[user_id] = 0

    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])

        if referrer_id != user_id and user_id not in referred_users:
            referred_users.add(user_id)
            if referrer_id not in user_balances:
                user_balances[referrer_id] = 0

            user_balances[referrer_id] += 2000

            try:
                ref_name = message.from_user.first_name or "Янги дўстингиз"
                await bot.send_message(
                    referrer_id,
                    f"🎉 <b>Табриклаймиз!</b>\n\n"
                    f"👥 Сизнинг реферал ҳаволангиз орқали <b>{ref_name}</b> ботга аъзо бўлди!\n"
                    f"💎 Ҳисобингизга <b>+2000 балл</b> қўшилди.",
                    parse_mode="HTML"
                )
            except Exception:
                pass

    save_users_data()
    user_name = message.from_user.first_name or "Қадрли инсон"

    welcome_text = (
        f"✨ <b>Ассалому алайкум ва роҳматуллоҳи ва барокатуҳ, {user_name}!</b>\n\n"
        f"🌙 <b>«Муборак Тасбеҳ ва зикрлар»</b> ботига хуш келибсиз!\n\n"
        f"<i>«Огоҳ бўлингизким, Аллоҳни зикр қилиш билан қалблар ором олур!»</i> (Раъд сураси, 28-оят).\n\n"
        f"👇 <i>Қуйидаги менюдан керакли бўлимни танланг:</i>"
    )

    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="HTML")

@dp.message(F.text == "⬅️ Асосий меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("✨ Асосий менюга қайтдингиз.", reply_markup=get_main_menu())

# 1. Т А С Б Е Х Н И  О Ч И Ш
@dp.message(F.text == "📿 Т А С Б Е Х Н И  О Ч И Ш")
async def open_tasbih(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Мини-иловани ишга тушириш", web_app=types.WebAppInfo(url=WEBAPP_URL))
    await message.answer(
        "📿 <b>Т А С Б Е Х!</b>\n\n"
        "Қуйидаги тугма орқали интерактив мини-иловага ўтинг ва зикр қилишни бошланг:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# 💰 Балансим
@dp.message(F.text == "💰 Балансим")
async def check_balance(message: types.Message):
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0)
    await message.answer(
        f"💰 <b>Сизнинг ҳисобингиз:</b>\n\n"
        f"💎 Жорий баланс: <b>{balance} балл</b>\n"
        f"💳 Энг кам пул ечиш миқдори: <b>500 000 балл</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

# 2. Пулни ечиб олиш
@dp.message(F.text == "💳 Пулни ечиб олиш")
async def process_withdrawal(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0)
    MIN_WITHDRAW = 500000

    if balance < MIN_WITHDRAW:
        needed = MIN_WITHDRAW - balance
        await message.answer(
            f"❌ <b>Пулни ечиб олиш учун балансингиз етарли эмас!</b>\n\n"
            f"💎 Жорий балансингиз: <b>{balance} балл</b>\n"
            f"📊 Энг кам миқдор: <b>{MIN_WITHDRAW} балл</b>\n"
            f"⚠️ Пул чиқариш учун яна <b>({needed})</b> балл етмайди.\n\n"
            "<i>Кўпроқ вазифаларни бажаринг ва дўстларингизни таклиф қилинг! (+2000 балл)</i>",
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
        return

    await message.answer(
        "💳 <b>Маблағни ечиб олиш маркази</b>\n\n"
        f"💎 Балансингиз етарли: <b>{balance} балл</b>\n\n"
        "Тўплаган балларни картага ёки телефон рақамига ўтказиш учун реквизитларингизни юборинг.\n\n"
        "<i>(Масалан: 8600 1234 5678 9012 / Исм Шариф ва банк номи)</i>\n\n"
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
    balance = user_balances.get(user.id, 0)

    if balance < 500000:
        await message.answer("❌ Балансингиз етарли эмас!", reply_markup=get_main_menu())
        await state.clear()
        return

    withdrawn_amount = balance
    user_balances[user.id] = 0
    save_users_data()

    admin_text = (
        f"🔔 <b>Янги пул чиқариш сўрови!</b>\n\n"
        f"👤 Фойдаланувчи: @{user.username or 'йўқ'} (ID: <code>{user.id}</code>)\n"
        f"Исми: {user.first_name}\n"
        f"💎 Ечилаётган сумма: <b>{withdrawn_amount} балл</b>\n"
        f"💳 Реквизит:\n<code>{details}</code>"
    )

    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Тўлаб берилди", callback_data=f"pay_yes_{user.id}_{withdrawn_amount}")
        builder.button(text="❌ Рад этиш", callback_data=f"pay_no_{user.id}_{withdrawn_amount}")
        builder.adjust(2)

        await bot.send_message(ADMIN_ID, admin_text, reply_markup=builder.as_markup(), parse_mode="HTML")

        await message.answer(
            "✅ <b>Сўровингиз қабул қилинди!</b>\n\n"
            "Администратор текширувидан кейин маблағ картангизга ўтказиб берилади.",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    except Exception:
        user_balances[user.id] += withdrawn_amount
        save_users_data()
        await message.answer("❌ Хатолик юз берди. Кейинроқ қайта уриниб кўринг.", reply_markup=get_main_menu())

    await state.clear()

@dp.callback_query(F.data.startswith("pay_"))
async def admin_payment_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Сизда бунинг учун ҳуқуқ йўқ!", show_alert=True)
        return

    parts = callback.data.split("_")
    action, user_id, amount = parts[1], int(parts[2]), int(parts[3])

    if action == "yes":
        await bot.send_message(user_id, "🎉 <b>Табриклаймиз!</b> Пул чиқариш сўровингиз тасдиқланди ва маблағ картангизга ўтказилди!", parse_mode="HTML")
        await callback.message.edit_text(callback.message.text + "\n\n<b>✅ Статус: ТЎЛАНДИ ВА ЯКУНЛАНДИ</b>", parse_mode="HTML")
    else:
        user_balances[user_id] = user_balances.get(user_id, 0) + amount
        save_users_data()
        await bot.send_message(user_id, f"❌ Афсус, сўровингиз рад этилди. <b>{amount} балл</b> балансингизга қайтарилди.", parse_mode="HTML")
        await callback.message.edit_text(callback.message.text + "\n\n<b>❌ Статус: РАД ЭТИЛДИ (Балл қайтарилди)</b>", parse_mode="HTML")

    await callback.answer("Бажарилди!")

# 🏆 Рейтинг
@dp.message(F.text == "🏆 Рейтинг")
async def show_leaderboard(message: types.Message):
    sorted_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)[:10]

    text = (
        "🏆 <b>Энг фаол фойдаланувчилар рейтинги (Топ-10)</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🏅 <b>Пешқадамлар рўйхати:</b>\n\n"
    )

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for index, (uid, balance) in enumerate(sorted_users):
        name = user_names.get(uid, f"Фойдаланувчи {uid}")
        medal = medals[index] if index < len(medals) else f"{index+1}."
        text += f"{medal} <b>{name}</b> — 💎 <b>{balance} балл</b>\n\n"

    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())

# 👥 Дўстларни таклиф
@dp.message(F.text == "👥 Дўстларни таклиф")
async def process_referral(message: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"

    await message.answer(
        "👥 <b>Дўстларни таклиф қилиш тизими</b>\n\n"
        "Яқинларингизни таклиф қилинг ва ҳар бир таклиф қилинган дўстингиз учун <b>2000 балл</b> олиб боринг!\n\n"
        "🔗 <b>Сизнинг шахсий линкингиз:</b>\n"
        f"<code>{ref_link}</code>",
        parse_mode="HTML"
    )

# 📋 Вазифалар
@dp.message(F.text == "📋 Вазифалар")
async def process_tasks(message: types.Message):
    global tasks_list
    tasks_list = load_tasks()
    
    if not tasks_list:
        await message.answer("📋 Ҳозирча янги вазифалар мавжуд эмас.", reply_markup=get_main_menu())
        return
    
    user_id = message.from_user.id
    completed_tasks_list = user_completed_tasks.get(user_id, [])
    
    active_tasks = [task for task in tasks_list if task['id'] not in completed_tasks_list]
    
    if not active_tasks:
        await message.answer(
            "🎉 <b>Табриклаймиз!</b>\n\nСиз барча мавжуд вазифаларни бажариб бўлдингиз.\nТегишли янги вазифалар қўшилишини кутинг!",
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
        return
    
    await message.answer("📋 <b>Кунлик вазифалар ва бонуслар</b>\n\nҚуйидаги вазифаларни бажариб баллар жамғаринг:", parse_mode="HTML")
    
    for task in active_tasks:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔗 Бажариш", url=task['url'])
        builder.button(text="🎁 Текшириш", callback_data=f"check_task_{task['id']}")
        builder.adjust(2)
        
        await message.answer(
            f"📌 <b>{task['title']}</b>\n🎁 Мукофот: <b>+{task['reward']} балл</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

@dp.callback_query(F.data.startswith(("check_task_", "noop_", "ok_task_")))
async def task_callback_handler(callback: types.CallbackQuery):
    if callback.data.startswith("noop_"):
        await callback.answer("Сиз бу вазифани аллақачон бажаргансиз!", show_alert=True)
        return

    if callback.data.startswith("ok_task_"):
        await callback.message.delete()
        return

    task_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    target_task = next((t for t in tasks_list if t['id'] == task_id), None)
    if not target_task:
        await callback.answer("Вазифа топилмади ёки муддати тугаган!", show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    if user_id not in user_completed_tasks:
        user_completed_tasks[user_id] = []

    if task_id in user_completed_tasks[user_id]:
        await callback.answer("Сиз бу вазифа учун аллақачон балл олгансиз!", show_alert=True)
        return

    url = target_task['url']
    if "t.me/" in url:
        channel_username = "@" + url.split("t.me/")[-1].strip("/").split("?")[0]
        try:
            member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if member.status in ["left", "kicked"]:
                await callback.answer(
                    "❌ Сиз ҳали каналга обуна бўлмагансиз!\nИлтимос, аввал обуна бўлинг ва кейин текширинг.",
                    show_alert=True
                )
                return
        except Exception:
            pass

    user_completed_tasks[user_id].append(task_id)
    user_balances[user_id] = user_balances.get(user_id, 0) + target_task['reward']
    save_users_data()

    await callback.answer("Вазифа муваффақиятли бажарилди!", show_alert=False)

    ok_builder = InlineKeyboardBuilder()
    ok_builder.button(text="OK", callback_data=f"ok_task_{task_id}")

    await callback.message.answer(
        f"✅ Ҳисобингизга <b>({target_task['reward']})</b> балл қўшилди!",
        reply_markup=ok_builder.as_markup(),
        parse_mode="HTML"
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

# ⭐ Рекламани кўриш
@dp.message(F.text == "⭐ Рекламани кўриш")
async def process_ads_view(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Рекламани кўриш ва қилинган зикрлар сонини сақлаб қолиш", web_app=types.WebAppInfo(url=WEBAPP_URL))
    await message.answer(
        "⭐ <b>Тасбеҳлар сони учиб кетмаслиги учун</b>\n\n"
        "Рекламани кўриш орқали лойиҳамизни қўллаб-қувватланг.",
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

@dp.message(F.text == "👥 Фойдаланувчилар")
async def admin_users_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not users:
        await message.answer("📭 Ҳозирча ботга кирган фойдаланувчилар йўқ.", reply_markup=get_admin_menu())
        return

    text = f"👥 <b>Ботдаги фойдаланувчилар рўйхати (Жами: {len(users)} та):</b>\n\n"

    for count, uid in enumerate(list(users)[-30:], start=1):
        name = user_names.get(uid, "Номаълум")
        balance = user_balances.get(uid, 0)
        text += f"{count}. {name} (ID: <code>{uid}</code>) — 💎 {balance} балл\n"

    if len(users) > 30:
        text += f"\n<i>...ва яна {len(users) - 30} та фойдаланувчи бор.</i>"

    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_menu())

@dp.message(F.text == "📢 Рассылка юбориш")
async def admin_broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminBroadcast.waiting_for_message)
    await message.answer(
        "📢 Барча фойдаланувчиларга юбормоқчи бўлган хабарингизни юборинг:\n\n"
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
        await message.answer(f"✍️ Фойдаланувчи (ID: {target_id}) учун қўшиладиган ёки айриладиган балл миқдорини киритинг (Масалан: <code>100</code> ёки <code>-50</code>):", parse_mode="HTML")
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

        user_balances[target_id] = user_balances.get(target_id, 0) + amount
        save_users_data()
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

@dp.message(F.text == "📋 Вазифа қўшиш")
async def admin_task_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminTask.waiting_title)
    await message.answer("✍️ Янги вазифа номини ва шартини киритинг (Масалан: <code>📢 Телеграм каналга обуна бўлиш</code>):", parse_mode="HTML")

@dp.message(AdminTask.waiting_title)
async def admin_task_get_title(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(title=message.text)
    await state.set_state(AdminTask.waiting_reward)
    await message.answer("💰 Ушбу вазифа учун бериладиган мукофот (балл) миқдорини рақамда киритинг (Масалан: <code>50</code>):", parse_mode="HTML")

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
    await state.update_data(url=url)
    await state.set_state(AdminTask.waiting_hours)
    await message.answer(
        "⏳ Вазифа қанча соат давомида амал қилишини киритинг:\n"
        "<i>(Масалан: <code>24</code> соат, <code>48</code> соат ёки чексиз бўлса <code>0</code> рақамини киритинг)</i>",
        parse_mode="HTML"
    )

@dp.message(AdminTask.waiting_hours)
async def admin_task_get_hours(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        hours = int(message.text)
        data = await state.get_data()
        title = data.get("title")
        reward = data.get("reward")
        url = data.get("url")
        
        expires_at = None
        if hours > 0:
            expires_at = time.time() + (hours * 3600)
            
        global tasks_list
        tasks_list = load_tasks() 
        
        new_id = max((t['id'] for t in tasks_list), default=0) + 1
        new_task = {
            "id": new_id, 
            "title": title, 
            "reward": reward, 
            "url": url,
            "expires_at": expires_at
        }
        
        tasks_list.append(new_task)
        save_tasks(tasks_list) 
        
        await state.clear()
        
        time_info = f"{hours} соат" if hours > 0 else "Чексиз (муддатсиз)"
        await message.answer(
            f"✅ <b>Янги вазифа муваффақиятли қўшилди!</b>\n\n"
            f"📌 Номи: {title}\n"
            f"🎁 Мукофот: {reward} балл\n"
            f"⏳ Амал қилиш муддати: {time_info}\n"
            f"🔗 Ҳавола: {url}",
            parse_mode="HTML",
            reply_markup=get_admin_menu()
        )
    except ValueError:
        await message.answer("❌ Фақат бутун рақам киритинг (масалан: 24 ёки 0):")

# Админ учун вазифаларни кўриш ва ўчириш менюси
@dp.message(F.text == "📋 Вазифаларни бошқариш")
async def admin_manage_tasks(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
        
    global tasks_list
    tasks_list = load_tasks()
    
    if not tasks_list:
        await message.answer("📭 Ҳозирча фаол вазифалар йўқ.", reply_markup=get_admin_menu())
        return
        
    await message.answer("📋 <b>Амалдаги вазифалар рўйхати:</b>\nКеракли вазифани ўчириш учун қуйидаги тугмани босинг:", parse_mode="HTML")
    
    for task in tasks_list:
        builder = InlineKeyboardBuilder()
        builder.button(text="🗑 Ўчириш (Бекор қилиш)", callback_data=f"del_task_{task['id']}")
        
        expires_str = "Чексиз"
        if task.get('expires_at'):
            remaining = int((task['expires_at'] - time.time()) / 3600)
            expires_str = f"Қолди: ~{remaining} соат" if remaining > 0 else "Муддати тугамоқда"

        await message.answer(
            f"📌 <b>{task['title']}</b>\n🎁 Мукофот: {task['reward']} балл\n⏳ Муддати: {expires_str}\n🔗 Ҳавола: {task['url']}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

# Вазифани ўчириш (callback) сўровини қабул қилиш
@dp.callback_query(F.data.startswith("del_task_"))
async def callback_delete_task(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Сизда бу ҳуқуқ йўқ!", show_alert=True)
        return
        
    task_id = int(callback.data.split("_")[2])
    
    remaining_tasks = delete_task_by_id(task_id)
    global tasks_list
    tasks_list = remaining_tasks
    
    await callback.answer("✅ Вазифа муваффақиятли ўчирилди!", show_alert=True)
    
    try:
        await callback.message.edit_text("❌ <b>Ушбу вазифа бекор қилинди ва ўчирилди.</b>", parse_mode="HTML")
    except Exception:
        pass

# Запуск бота
async def main():
    print("Тасбеҳ боти муваффақиятли ишга тушди...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

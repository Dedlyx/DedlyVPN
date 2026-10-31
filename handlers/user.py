from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from keyboards.user_kb import main_menu, back_main, shop_kb, profile_kb, help_kb
from database import db
from config import ADMIN_ID
from datetime import datetime
import time

router = Router()
SUPPORT_LINK = "https://t.me/your_support_username" # ЗАМЕНИ НА СВОЙ НИК!

async def safe_edit(callback: CallbackQuery, text: str, kb=None):
    try:
        if callback.message.caption is not None:
            await callback.message.edit_caption(caption=text, reply_markup=kb)
        else:
            await callback.message.edit_text(text=text, reply_markup=kb)
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            try:
                await callback.message.answer(text, reply_markup=kb)
            except:
                pass

@router.message(CommandStart())
async def cmd_start(message: Message):
    referrer_id = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].split("_")[1])
            if referrer_id == message.from_user.id: referrer_id = None
        except: pass

    await db.create_user(message.from_user.id, message.from_user.username, referrer_id)
    user = await db.get_user(message.from_user.id)
    
    balance = float(user[2]) if user[2] else 0.0
    
    text = (
        "🔥 <b>Добро пожаловать в SpaceVPN — твой ключ к свободному интернету!</b>\n\n"
        "<blockquote>🛡 <b>Почему выбирают нас?</b>\n"
        "✅ Максимальная скорость до 1 Гбит/с\n"
        "✅ Обход любых блокировок (YouTube, Instagram, Discord)\n"
        "✅ Полная анонимность и отсутствие логов\n"
        "✅ Стабильные сервера 24/7</blockquote>\n"
        f"💰 <i>Твой текущий баланс:</i> <b>{balance:.2f} ₽</b>\n\n"
        "👇 Выбери нужное действие в меню ниже:"
    )
    
    photo_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop"
    
    try:
        await message.answer_photo(photo=photo_url, caption=text, reply_markup=main_menu())
    except Exception:
        await message.answer(text, reply_markup=main_menu())

@router.callback_query(F.data == "back_main")
async def back_main_handler(callback: CallbackQuery):
    await callback.answer()
    user = await db.get_user(callback.from_user.id)
    balance = float(user[2]) if user[2] else 0.0
    text = (
        "🚀 <b>Главное меню</b>\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        f"💳 Ваш баланс: <b>{balance:.2f} ₽</b>"
    )
    try:
        await callback.message.delete()
    except: pass
    await callback.message.answer(text, reply_markup=main_menu())

# ===== ПОМОЩЬ =====
@router.callback_query(F.data == "help_menu")
async def show_help(callback: CallbackQuery):
    await callback.answer()
    text = "📚 <b>Центр помощи</b>\n\nЗдесь вы найдете ответы на все вопросы. Если что-то непонятно, наша поддержка всегда на связи!"
    await safe_edit(callback, text, help_kb(SUPPORT_LINK))

@router.callback_query(F.data == "help_instructions")
async def help_instructions(callback: CallbackQuery):
    await callback.answer()
    text = (
        "📖 <b>Как начать пользоваться?</b>\n\n"
        "1️⃣ <b>Пополните баланс</b> в разделе «💰 Пополнить баланс».\n"
        "2️⃣ <b>Купите подписку</b> в разделе «🛒 Купить / Продлить».\n"
        "3️⃣ <b>Дождитесь ссылки</b> (мы выдадим ее в течение 5-15 минут).\n"
        "4️⃣ <b>Скопируйте ключ</b> из профиля и вставьте его в приложение.\n\n"
        "Если возникли сложности — пишите в поддержку!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="help_menu")]])
    await safe_edit(callback, text, kb)

@router.callback_query(F.data == "help_why_us")
async def help_why_us(callback: CallbackQuery):
    await callback.answer()
    text = (
        "💎 <b>Наши главные преимущества</b>\n\n"
        "⚡ <b>Скорость:</b> Протокол VLESS, который не режет скорость и идеально подходит для 4K.\n"
        "🌍 <b>Локации:</b> Сервера в Европе и Азии.\n"
        "🔒 <b>Безопасность:</b> Трафик зашифрован. Мы не собираем статистику.\n"
        "🤝 <b>Честность:</b> Если сервис вам не подойдет, мы вернем деньги."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="help_menu")]])
    await safe_edit(callback, text, kb)

# ===== ЛИЧНЫЙ КАБИНЕТ =====
@router.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery):
    await callback.answer("Подписка проверена! Нажмите /start еще раз.", show_alert=True)

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    if not user:
        await db.create_user(callback.from_user.id, callback.from_user.username)
        user = await db.get_user(callback.from_user.id)

    try:
        user_id = user[0]
        username = f"@{user[1]}" if user[1] else "Не указан"
        
        balance = float(user[2]) if user[2] else 0.0
        sub_end_ts = int(user[3]) if user[3] else 0
        vpn_link = user[4] if user[4] else "Ожидает выдачи"
        devices = int(user[5]) if user[5] else 2
        traffic = float(user[6]) if user[6] else 0.0
        reg_date = str(user[10]) if len(user) > 10 and user[10] else "Неизвестно"
        
        if sub_end_ts > int(time.time()):
            sub_end = datetime.fromtimestamp(sub_end_ts).strftime("%d.%m.%Y %H:%M")
            status_icon = "🟢"
        else:
            sub_end = "❌ Не активна"
            status_icon = "🔴"

        filled = int((traffic / 100.0) * 10) if traffic > 0 else 0
        bar = "🟩" * filled + "⬛️" * (10 - filled)

        text = (
            f"<blockquote>👤 <b>Личный кабинет</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📧 Юзернейм: <code>{username}</code>\n"
            f"📅 С нами с: {reg_date}\n\n"
            f"ℹ️ <b>Ваша подписка:</b>\n"
            f"├ Статус: {status_icon} <b>{sub_end}</b>\n"
            f"├ Устройств: <b>{devices}</b>\n"
            f"└ Ваш ключ: <code>{vpn_link}</code>\n\n"
            f"📊 <b>Трафик:</b>\n"
            f"{bar}\n"
            f"Осталось: <b>{traffic} ГБ</b></blockquote>\n\n"
            f"💳 <b>Баланс:</b> {balance:.2f} ₽"
        )
        await safe_edit(callback, text, profile_kb())
    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка при загрузке профиля. Нажмите /start\n\n(Код: {e})")

# ===== МАГАЗИН =====
@router.callback_query(F.data == "shop")
async def show_shop(callback: CallbackQuery):
    await callback.answer()
    text = "🛒 <b>Магазин подписок</b>\n\n<blockquote>Вы можете купить подписку или попробовать наш сервис на 3 дня по специальной цене.</blockquote>"
    await safe_edit(callback, text, shop_kb())

@router.callback_query(F.data.in_(["shop_buy", "shop_extend", "shop_trial"]))
async def show_tariffs(callback: CallbackQuery):
    await callback.answer()
    action = callback.data.split("_")[1]
    
    if action == "trial":
        p_rub = await db.get_setting('price_trial')
        text = (
            "🔥 <b>Пробный период на 3 дня</b>\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
            f"Стоимость: <b>{p_rub} ₽</b>\n\n"
            "Оцените скорость и стабильность нашего VPN!"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💳 Купить за {p_rub} ₽", callback_data="buy_trial")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="shop")]
        ])
    else:
        p28, p14, p5 = await db.get_setting('price_28'), await db.get_setting('price_14'), await db.get_setting('price_5')
        text = "📦 <b>Выберите тарифный план</b>\n➖➖➖➖➖➖➖➖➖➖\nЦены указаны в рублях."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📦 28 дней — {p28} ₽", callback_data=f"{action}_28")],
            [InlineKeyboardButton(text=f"📦 14 дней — {p14} ₽", callback_data=f"{action}_14")],
            [InlineKeyboardButton(text=f"📦 5 дней — {p5} ₽", callback_data=f"{action}_5")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="shop")]
        ])

    await safe_edit(callback, text, kb)

# ===== ИСПРАВЛЕННАЯ ПОКУПКА =====
@router.callback_query(F.data.startswith(("buy_", "ext_")))
async def process_buy(callback: CallbackQuery):
    await callback.answer()
    
    try:
        action_data = callback.data.split("_")[1]
        
        if action_data == "trial":
            user = await db.get_user(callback.from_user.id)
            if not user:
                await callback.message.answer("Нажмите /start для регистрации.")
                return
            if int(user[9]) == 1:
                await callback.answer("❌ Вы уже использовали пробный период!", show_alert=True)
                return
            
            price_str = await db.get_setting('price_trial')
            price = float(price_str) if price_str else 22.0
            days = 3
            await db.use_trial(callback.from_user.id)
        else:
            days = int(action_data)
            price_str = await db.get_setting(f'price_{days}')
            price = float(price_str) if price_str else 0.0
        
        user = await db.get_user(callback.from_user.id)
        if not user:
            await callback.message.answer("Нажмите /start для регистрации.")
            return
            
        balance = float(user[2]) if user[2] else 0.0
        
        if balance < price:
            await callback.answer(f"❌ Недостаточно средств!\nБаланс: {balance:.2f} ₽\nНужно: {price} ₽", show_alert=True)
            return

        # Списываем баланс и создаем заявку
        await db.update_balance(callback.from_user.id, -price)
        purchase_id = await db.create_purchase(callback.from_user.id, callback.from_user.username, days, price)

        text = (
            f"⏳ <b>Заявка на покупку создана!</b>\n\n"
            f"Списано: <b>{price} ₽</b>\n"
            f"Ожидайте, администратор выдаст вам ссылку.\n"
            f"<i>Обычно это занимает до 30 минут.</i>"
        )
        await safe_edit(callback, text, back_main())

        # Отправка уведомления админу (с защитой от ошибок)
        try:
            await callback.bot.send_message(
                ADMIN_ID,
                f"🔔 <b>Новая заявка #{purchase_id}</b>\n"
                f"👤 @{callback.from_user.username} (ID: {callback.from_user.id})\n"
                f"📦 {days} дней | 💰 {price} ₽",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👑 Выдать ссылку", callback_data="admin_main")]])
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления админу: {e}")

    except Exception as e:
        # Если что-то пошло не так, пользователь увидит ошибку
        await callback.message.answer(f"⚠️ Ошибка при создании заявки: {e}")

# ===== РЕФЕРАЛКА =====
@router.callback_query(F.data == "referral")
async def show_ref(callback: CallbackQuery):
    await callback.answer()
    user = await db.get_user(callback.from_user.id)
    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user[0]}"
    percent = await db.get_setting('ref_percent')
    
    text = (
        "🎁 <b>Партнерская программа</b>\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        f"Приглашайте друзей и получайте <b>{percent}%</b> от каждого их пополнения на ваш баланс!\n\n"
        "Чем больше друг пополнит, тем больше вы заработаете.\n\n"
        f"🔗 <b>Ваша ссылка:</b>\n<code>{ref_link}</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться", url=f"https://t.me/share/url?url={ref_link}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])
    await safe_edit(callback, text, kb)
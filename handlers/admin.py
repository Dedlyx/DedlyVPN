from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from keyboards.admin_kb import (admin_panel, admin_back, admin_pending_buys_list, 
                                admin_buy_details, admin_prices_menu, admin_edit_item_kb,
                                admin_pending_checks_list, admin_check_details)
from database import db
import asyncio

router = Router()

async def safe_edit(callback: CallbackQuery, text: str, kb=None):
    try:
        if callback.message.caption is not None:
            await callback.message.edit_caption(caption=text, reply_markup=kb)
        else:
            await callback.message.edit_text(text=text, reply_markup=kb)
    except Exception:
        try:
            await callback.message.answer(text, reply_markup=kb)
        except:
            pass

class AdminStates(StatesGroup):
    set_bank_name = State()
    set_bank_card = State()
    give_link = State()
    give_admin_acc = State()
    edit_price_rub = State()
    edit_price_star = State()
    broadcast_msg = State()

@router.message(Command("admin"))
async def admin_cmd(message: Message):
    if message.from_user.id != ADMIN_ID: return
    total, active, expiring, pending_checks, pending_buys, turnover, subs_sold = await db.get_stats()
    text = (
        "👑 <b>Панель управления</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"🟢 Активных подписок: <b>{active}</b>\n"
        f"⏳ Истекают (3 дня): <b>{expiring}</b>\n\n"
        f"💵 <b>Оборот за всё время:</b> <b>{turnover:.2f} ₽</b>\n"
        f"📦 <b>Продано подписок:</b> <b>{subs_sold}</b>\n\n"
        f"🧾 Чеков на проверку: <b>{pending_checks}</b>\n"
        f"📥 Заявок на покупку: <b>{pending_buys}</b>"
    )
    await message.answer(text, reply_markup=admin_panel())

@router.callback_query(F.data == "admin_main")
async def admin_main(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    if callback.from_user.id != ADMIN_ID: return
    total, active, expiring, pending_checks, pending_buys, turnover, subs_sold = await db.get_stats()
    text = (
        "👑 <b>Панель управления</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"🟢 Активных подписок: <b>{active}</b>\n"
        f"⏳ Истекают (3 дня): <b>{expiring}</b>\n\n"
        f"💵 <b>Оборот за всё время:</b> <b>{turnover:.2f} ₽</b>\n"
        f"📦 <b>Продано подписок:</b> <b>{subs_sold}</b>\n\n"
        f"🧾 Чеков на проверку: <b>{pending_checks}</b>\n"
        f"📥 Заявок на покупку: <b>{pending_buys}</b>"
    )
    await safe_edit(callback, text, admin_panel())

# ===== ЧЕКИ =====
@router.callback_query(F.data == "adm_pending_checks")
async def adm_pending_checks(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id != ADMIN_ID: return
    checks = await db.get_pending_checks()
    
    if not checks:
        await safe_edit(callback, "✅ Нет чеков, ожидающих проверки.", admin_back())
        return
        
    text = "🧾 <b>Чеки на проверку:</b>\nВыберите чек для просмотра:"
    await safe_edit(callback, text, admin_pending_checks_list(checks))

@router.callback_query(F.data.startswith("adm_view_check_"))
async def adm_view_check(callback: CallbackQuery):
    await callback.answer()
    check_id = int(callback.data.split("_")[3])
    ch = await db.get_check(check_id)
    
    if not ch or ch[5] != 'pending':
        await callback.answer("Этот чек уже обработан!", show_alert=True)
        return
        
    text = f"🧾 <b>Чек #{ch[0]}</b>\n\n👤 От: <code>{ch[1]}</code>\n📝 Имя: <b>{ch[3]}</b>\n💰 Сумма: <b>{ch[2]} ₽</b>"
    file_id = ch[4]
    
    if not file_id:
        await callback.message.answer(text + "\n\n⚠️ <i>Файл чека отсутствует</i>", reply_markup=admin_check_details(check_id))
        return

    try:
        # Пробуем отправить как фото
        await callback.message.answer_photo(photo=file_id, caption=text, reply_markup=admin_check_details(check_id))
    except Exception:
        try:
            # Пробуем как документ
            await callback.message.answer_document(document=file_id, caption=text, reply_markup=admin_check_details(check_id))
        except Exception:
            await callback.message.answer(text + "\n\n⚠️ <i>Не удалось загрузить фото</i>", reply_markup=admin_check_details(check_id))
            
    try:
        await callback.message.delete()
    except:
        pass

# ===== УПРАВЛЕНИЕ ЦЕНАМИ =====
@router.callback_query(F.data == "adm_prices")
async def adm_prices(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id != ADMIN_ID: return
    p28, p14, p5, pt = await db.get_setting('price_28'), await db.get_setting('price_14'), await db.get_setting('price_5'), await db.get_setting('price_trial')
    s28, s14, s5, st = await db.get_setting('stars_28'), await db.get_setting('stars_14'), await db.get_setting('stars_5'), await db.get_setting('stars_trial')
    
    text = (
        "💵 <b>Управление ценами</b>\n\n"
        f"28 дней: <b>{p28} ₽</b> / {s28} ⭐\n"
        f"14 дней: <b>{p14} ₽</b> / {s14} ⭐\n"
        f"5 дней: <b>{p5} ₽</b> / {s5} ⭐\n"
        f"Пробный (3д): <b>{pt} ₽</b> / {st} ⭐\n\n"
        "Выберите, что редактировать:"
    )
    await safe_edit(callback, text, admin_prices_menu())

@router.callback_query(F.data.startswith("adm_edit_price_"))
async def adm_edit_price_menu(callback: CallbackQuery):
    await callback.answer()
    item = callback.data.split("_")[3]
    p = await db.get_setting(f'price_{item}')
    s = await db.get_setting(f'stars_{item}')
    text = f"⚙️ <b>Редактирование: {item}</b>\n\nТекущая цена: {p} ₽ / {s} ⭐"
    await safe_edit(callback, text, admin_edit_item_kb(item))

@router.callback_query(F.data.startswith("adm_set_rub_"))
async def adm_set_rub(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    item = callback.data.split("_")[3]
    await state.update_data(edit_item=item)
    await state.set_state(AdminStates.edit_price_rub)
    await safe_edit(callback, f"Введите новую цену в <b>рублях</b> для тарифа {item}:")

@router.message(AdminStates.edit_price_rub)
async def save_rub(message: Message, state: FSMContext):
    data = await state.get_data()
    item = data['edit_item']
    if not message.text.isdigit():
        await message.answer("Введите целое число!")
        return
    await db.set_setting(f'price_{item}', message.text)
    await state.clear()
    await message.answer(f"✅ Цена в рублях для {item} обновлена!", reply_markup=admin_back())

@router.callback_query(F.data.startswith("adm_set_star_"))
async def adm_set_star(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    item = callback.data.split("_")[3]
    await state.update_data(edit_item=item)
    await state.set_state(AdminStates.edit_price_star)
    await safe_edit(callback, f"Введите новую цену в <b>звездах</b> для тарифа {item}:")

@router.message(AdminStates.edit_price_star)
async def save_star(message: Message, state: FSMContext):
    data = await state.get_data()
    item = data['edit_item']
    if not message.text.isdigit():
        await message.answer("Введите целое число!")
        return
    await db.set_setting(f'stars_{item}', message.text)
    await state.clear()
    await message.answer(f"✅ Цена в звездах для {item} обновлена!", reply_markup=admin_back())

# ===== ЗАЯВКИ НА ПОКУПКУ =====
@router.callback_query(F.data == "adm_pending_buys")
async def adm_pending_buys(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id != ADMIN_ID: return
    purchases = await db.get_pending_purchases()
    
    if not purchases:
        await safe_edit(callback, "✅ Нет активных заявок на покупку.", admin_back())
        return
        
    text = "📥 <b>Активные заявки на покупку:</b>\nВыберите заявку для выдачи ссылки:"
    await safe_edit(callback, text, admin_pending_buys_list(purchases))

@router.callback_query(F.data.startswith("adm_view_buy_"))
async def adm_view_buy(callback: CallbackQuery):
    await callback.answer()
    purchase_id = int(callback.data.split("_")[3])
    p = await db.get_purchase(purchase_id)
    text = (
        f"📦 <b>Заявка #{p[0]}</b>\n\n"
        f"👤 Юзер: @{p[2]} (ID: <code>{p[1]}</code>)\n"
        f"📅 Тариф: <b>{p[3]} дней</b>\n"
        f"💰 Сумма: <b>{p[4]} ₽</b>\n"
        f"🕒 Создана: {p[6]}"
    )
    await safe_edit(callback, text, admin_buy_details(purchase_id))

@router.callback_query(F.data.startswith("adm_give_link_"))
async def adm_give_link(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.from_user.id != ADMIN_ID: return
    purchase_id = int(callback.data.split("_")[3])
    await state.update_data(purchase_id=purchase_id)
    await state.set_state(AdminStates.give_link)
    p = await db.get_purchase(purchase_id)
    await safe_edit(callback, f"🔗 <b>Выдача для @{p[2]} (Заявка #{p[0]})</b>\n\nОтправьте ссылку на подписку (или ключ):")

@router.message(AdminStates.give_link)
async def adm_save_link(message: Message, state: FSMContext):
    await state.update_data(vpn_link=message.text)
    await state.set_state(AdminStates.give_admin_acc)
    await message.answer("Теперь введите <b>ваш аккаунт</b> (для истории):\nНапример: <code>@my_acc_1</code>")

@router.message(AdminStates.give_admin_acc)
async def adm_save_admin_acc(message: Message, state: FSMContext):
    data = await state.get_data()
    purchase_id = data['purchase_id']
    vpn_link = data['vpn_link']
    admin_acc = message.text
    await state.clear()
    
    p = await db.get_purchase(purchase_id)
    await db.approve_purchase(purchase_id, p[1], p[3], vpn_link, admin_acc)
    
    await message.answer(f"✅ Ссылка выдана юзеру @{p[2]}", reply_markup=admin_back())
    await message.bot.send_message(p[1], f"🎉 <b>Ваша подписка активирована!</b>\n\n🔗 Ссылка:\n<code>{vpn_link}</code>\n\nИнструкция в разделе Помощь.")

# ===== ОБРАБОТКА КНОПОК ЧЕКА =====
@router.callback_query(F.data.startswith("adm_ok_check_"))
async def ok_check(callback: CallbackQuery):
    await callback.answer()
    check_id = int(callback.data.split("_")[3])
    check = await db.get_check(check_id)
    
    if check[5] == 'pending':
        await db.update_balance(check[1], check[2])
        await db.set_check_status(check_id, 'approved')
        
        new_caption = (callback.message.caption or callback.message.text) + "\n\n✅ <b>ЗАЧИСЛЕНО</b>"
        
        try:
            if callback.message.caption is not None:
                await callback.message.edit_caption(caption=new_caption)
            else:
                await callback.message.edit_text(text=new_caption)
        except Exception:
            pass
            
        await callback.bot.send_message(check[1], f"🎉 Баланс пополнен на {check[2]} ₽!")
    else:
        await callback.answer("Этот чек уже обработан!", show_alert=True)

@router.callback_query(F.data.startswith("adm_no_check_"))
async def no_check(callback: CallbackQuery):
    await callback.answer()
    check_id = int(callback.data.split("_")[3])
    check = await db.get_check(check_id)
    
    if check[5] == 'pending':
        await db.set_check_status(check_id, 'rejected')
        
        new_caption = (callback.message.caption or callback.message.text) + "\n\n❌ <b>ОТКЛОНЕНО</b>"
        
        try:
            if callback.message.caption is not None:
                await callback.message.edit_caption(caption=new_caption)
            else:
                await callback.message.edit_text(text=new_caption)
        except Exception:
            pass
            
        await callback.bot.send_message(check[1], "⚠️ Ваш чек отклонен. Попробуйте снова или напишите в поддержку.")
    else:
        await callback.answer("Этот чек уже обработан!", show_alert=True)

@router.callback_query(F.data.startswith("adm_no_buy_"))
async def no_buy(callback: CallbackQuery):
    await callback.answer()
    purchase_id = int(callback.data.split("_")[3])
    p = await db.get_purchase(purchase_id)
    await db.reject_purchase(purchase_id, p[1], p[4])
    await safe_edit(callback, callback.message.text + "\n\n❌ <b>ОТКЛОНЕНО (Деньги возвращены)</b>")
    await callback.bot.send_message(p[1], f"⚠️ Ваша заявка отклонена. Баланс пополнен на {p[4]} ₽.")

# ===== РАССЫЛКА И НАСТРОЙКИ =====
@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminStates.broadcast_msg)
    await safe_edit(callback, "📢 Введите сообщение для рассылки всем пользователям (можно с фото):")

@router.message(AdminStates.broadcast_msg)
async def adm_broadcast_send(message: Message, state: FSMContext):
    await state.clear()
    users = await db.get_all_users()
    await message.answer(f"⏳ Рассылка запущена для {len(users)} юзеров...")
    
    success, fail = 0, 0
    for u_id in users:
        try:
            await message.copy_to(chat_id=u_id)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1
            
    await message.answer(f"✅ <b>Рассылка завершена!</b>\n\nУспешно: {success}\nЗаблокировали: {fail}", reply_markup=admin_back())

@router.callback_query(F.data == "adm_settings")
async def adm_settings(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id != ADMIN_ID: return
    bank = await db.get_setting('bank_name')
    card = await db.get_setting('bank_card')
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить Банк", callback_data="set_bank_name")],
        [InlineKeyboardButton(text="Изменить Карту", callback_data="set_bank_card")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ])
    await safe_edit(callback, f"⚙️ <b>Реквизиты</b>\n\nБанк: <b>{bank}</b>\nКарта: <code>{card}</code>", kb)

@router.callback_query(F.data == "set_bank_name")
async def set_bname(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminStates.set_bank_name)
    await safe_edit(callback, "Введите новое название банка:")

@router.message(AdminStates.set_bank_name)
async def save_bname(message: Message, state: FSMContext):
    await db.set_setting('bank_name', message.text)
    await state.clear()
    await message.answer("✅ Банк обновлен!", reply_markup=admin_back())

@router.callback_query(F.data == "set_bank_card")
async def set_bcard(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminStates.set_bank_card)
    await safe_edit(callback, "Введите новый номер карты:")

@router.message(AdminStates.set_bank_card)
async def save_bcard(message: Message, state: FSMContext):
    await db.set_setting('bank_card', message.text)
    await state.clear()
    await message.answer("✅ Карта обновлена!", reply_markup=admin_back())

@router.callback_query(F.data == "adm_table")
async def adm_table(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id != ADMIN_ID: return
    purchases = await db.get_all_purchases(10)
    
    if not purchases:
        await safe_edit(callback, "Таблица пуста.", admin_back())
        return

    text = "📊 <b>Последние 10 операций:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for p in purchases:
        status_icon = "🟢" if p[5] == 'completed' else "⏳"
        text += f"{status_icon} <b>#{p[0]}</b> | @{p[2]} | {p[3]} дн. | {p[4]}₽\n"
        
    await safe_edit(callback, text, admin_back())
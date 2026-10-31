from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from keyboards.user_kb import topup_kb, back_main, cancel_kb
from database import db
from config import ADMIN_ID

router = Router()

class TopUp(StatesGroup):
    amount = State()
    comment = State()
    receipt = State()

@router.callback_query(F.data == "topup_menu")
async def show_topup(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("💰 <b>Пополнение баланса</b>\nВыберите способ:", reply_markup=topup_kb())

@router.callback_query(F.data == "soon")
async def soon(callback: CallbackQuery):
    await callback.answer("Этот способ оплаты появится совсем скоро!", show_alert=True)

@router.callback_query(F.data == "topup_bank")
async def bank_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(TopUp.amount)
    await callback.message.edit_text(
        "🏦 <b>Пополнение через банк</b>\n\n"
        "Введите сумму пополнения в рублях (только число):\n"
        "Например: <code>500</code>", 
        reply_markup=cancel_kb()
    )

@router.message(TopUp.amount)
async def bank_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount < 50: 
            await message.answer("Минимальная сумма — 50 руб. Введите еще раз:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите число (например, 300):")
        return

    await state.update_data(amount=amount)
    await state.set_state(TopUp.comment)
    
    await message.answer(
        f"✅ Сумма: <b>{amount} ₽</b>\n\n"
        "Шаг 2 из 3. Напишите ваше <b>Имя или Фамилию</b> (чтобы админ понял, от кого перевод):\n"
        "Например: <code>Иван Иванов</code>"
    )

@router.message(TopUp.comment)
async def bank_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    await state.update_data(comment=comment)
    await state.set_state(TopUp.receipt)
    
    data = await state.get_data()
    amount = data['amount']
    
    card = await db.get_setting('bank_card')
    bank = await db.get_setting('bank_name')

    await message.answer(
        f"🏦 <b>Реквизиты для перевода:</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"Банк: <b>{bank}</b>\n"
        f"Карта: <code>{card}</code>\n"
        f"Сумма: <b>{amount} ₽</b>\n"
        f"От кого: <b>{comment}</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n\n"
        "⚠️ <i>Переведите точную сумму и отправьте сюда <b>ФОТО или ФАЙЛ</b> чека.</i>"
    )

@router.message(TopUp.receipt, F.photo | F.document)
async def bank_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data['amount']
    comment = data['comment']
    await state.clear()
    
    file_id = ""
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    
    check_id = await db.add_check(message.from_user.id, amount, comment, file_id)
    
    from keyboards.admin_kb import admin_check_details
    admin_text = (
        f"🔔 <b>Новый чек на пополнение #{check_id}</b>\n\n"
        f"👤 От: @{message.from_user.username}\n"
        f"📝 Имя: <b>{comment}</b>\n"
        f"💰 Сумма: <b>{amount} ₽</b>"
    )
    admin_kb = admin_check_details(check_id)

    try:
        # Пытаемся отправить как фото
        if message.photo:
            await message.bot.send_photo(ADMIN_ID, photo=file_id, caption=admin_text, reply_markup=admin_kb)
        # Если это файл
        elif message.document:
            await message.bot.send_document(ADMIN_ID, document=file_id, caption=admin_text, reply_markup=admin_kb)
    except Exception as e:
        # Если первая попытка провалилась, пробуем отправить копию сообщения
        try:
            await message.copy_to(chat_id=ADMIN_ID, caption=admin_text, reply_markup=admin_kb)
        except Exception as e2:
            await message.bot.send_message(ADMIN_ID, admin_text + f"\n\n<i>⚠️ Ошибка фото: {e} | {e2}</i>", reply_markup=admin_kb)
    
    await message.answer(
        "✅ Чек успешно отправлен администратору на проверку.\nОжидайте зачисления!", 
        reply_markup=back_main()
    )

@router.message(TopUp.receipt)
async def bank_wrong_format(message: Message):
    await message.answer("⚠️ Пожалуйста, отправьте <b>скриншот</b> (фото) или <b>файл</b> с чеком.")
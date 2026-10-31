from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_panel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Заявки на покупку", callback_data="adm_pending_buys")],
        [InlineKeyboardButton(text="🧾 Чеки на пополнение", callback_data="adm_pending_checks")],
        [InlineKeyboardButton(text="📊 Таблица операций", callback_data="adm_table")],
        [InlineKeyboardButton(text="💵 Управление ценами", callback_data="adm_prices")],
        [InlineKeyboardButton(text="⚙️ Реквизиты карты", callback_data="adm_settings")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="🔙 Закрыть", callback_data="back_main")]
    ])

def admin_pending_checks_list(checks):
    kb = []
    for ch in checks:
        kb.append([InlineKeyboardButton(text=f"#{ch[0]} | {ch[3]} | {ch[2]} ₽", callback_data=f"adm_view_check_{ch[0]}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_check_details(check_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Зачислить", callback_data=f"adm_ok_check_{check_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_check_{check_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="adm_pending_checks")]
    ])

def admin_prices_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="28 дней", callback_data="adm_edit_price_28")],
        [InlineKeyboardButton(text="14 дней", callback_data="adm_edit_price_14")],
        [InlineKeyboardButton(text="5 дней", callback_data="adm_edit_price_5")],
        [InlineKeyboardButton(text="Пробный (3 дня)", callback_data="adm_edit_price_trial")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ])

def admin_edit_item_kb(item):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить цену в ₽", callback_data=f"adm_set_rub_{item}")],
        [InlineKeyboardButton(text="Изменить цену в ⭐", callback_data=f"adm_set_star_{item}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="adm_prices")]
    ])

def admin_pending_buys_list(purchases):
    kb = []
    for p in purchases:
        kb.append([InlineKeyboardButton(text=f"#{p[0]} | @{p[2]} | {p[3]} дн.", callback_data=f"adm_view_buy_{p[0]}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_buy_details(purchase_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Выдать ссылку", callback_data=f"adm_give_link_{purchase_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_buy_{purchase_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="adm_pending_buys")]
    ])

def admin_back():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_main")]])
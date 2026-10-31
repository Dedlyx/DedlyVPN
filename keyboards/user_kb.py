from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="profile")],
        [InlineKeyboardButton(text="🛒 Купить / Продлить VPN", callback_data="shop")],
        [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="topup_menu")],
        [InlineKeyboardButton(text="📚 Инструкции и Помощь", callback_data="help_menu")],
        [InlineKeyboardButton(text="🎁 Пригласить друга (15%)", callback_data="referral")]
    ])

def back_main():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_main")]])

def help_kb(support_link):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Как начать работу?", callback_data="help_instructions")],
        [InlineKeyboardButton(text="💎 Наши преимущества", callback_data="help_why_us")],
        [InlineKeyboardButton(text="🆘 Служба поддержки", url=support_link)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])

def profile_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Продлить подписку", callback_data="shop_extend")],
        [InlineKeyboardButton(text="🛒 Купить новую", callback_data="shop_buy")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])

def shop_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Купить подписку", callback_data="shop_buy")],
        [InlineKeyboardButton(text="🎁 Пробный период (3 дня)", callback_data="shop_trial")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])

def topup_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 Банковский перевод", callback_data="topup_bank")],
        [InlineKeyboardButton(text="🌟 Telegram Stars (Скоро)", callback_data="soon")],
        [InlineKeyboardButton(text="🪙 Криптовалюта (Скоро)", callback_data="soon")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])

def cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="back_main")]])
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import SPONSOR_CHANNEL, ADMIN_ID

class CheckSubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        if user_id == ADMIN_ID:
            return await handler(event, data)
            
        try:
            member = await event.bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
            if member.status in ['left', 'kicked']:
                raise Exception("Not subscribed")
        except Exception:
            text = "⚠️ <b>Для использования бота, пожалуйста, подпишитесь на наш канал!</b>"
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Подписаться", url=f"https://t.me/{SPONSOR_CHANNEL.replace('@', '')}")],
                [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
            ])
            if isinstance(event, Message):
                await event.answer(text, reply_markup=kb)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(text, reply_markup=kb)
                await event.answer()
            return
            
        return await handler(event, data)
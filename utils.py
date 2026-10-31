from aiogram.types import CallbackQuery, InlineKeyboardMarkup

async def safe_edit(callback: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup = None):
    """
    Умное редактирование сообщения.
    Если это фото — меняет подпись. Если текст — меняет текст.
    Если ничего не выходит — удаляет старое и шлет новое.
    """
    try:
        if callback.message.text:
            await callback.message.edit_text(text, reply_markup=reply_markup)
        else:
            await callback.message.edit_caption(caption=text, reply_markup=reply_markup)
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=reply_markup)
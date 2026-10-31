import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from database import db
from middlewares.subscription import CheckSubscriptionMiddleware
from handlers import user, payment, admin
from keyboards.user_kb import main_menu

# Фоновая задача для проверки подписок
async def check_subscriptions_worker(bot: Bot):
    while True:
        try:
            users = await db.get_expiring_users()
            for u_id, sub_end_ts in users:
                try:
                    await bot.send_message(
                        u_id,
                        "⚠️ <b>Внимание!</b>\n\n"
                        "Ваша подписка на VPN заканчивается через <b>3 дня</b>.\n"
                        "Пожалуйста, продлите её заранее в разделе «🛒 Купить / Продлить», чтобы не остаться без связи!",
                        reply_markup=main_menu()
                    )
                    await db.mark_notified(u_id)
                except Exception:
                    pass 
                    
        except Exception as e:
            logging.error(f"Ошибка в воркере уведомлений: {e}")
            
        await asyncio.sleep(3600)

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    await db.init_db()

    dp.message.middleware(CheckSubscriptionMiddleware())
    dp.callback_query.middleware(CheckSubscriptionMiddleware())

    dp.include_router(admin.router)
    dp.include_router(user.router)
    dp.include_router(payment.router)

    asyncio.create_task(check_subscriptions_worker(bot))

    print("Бот успешно запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
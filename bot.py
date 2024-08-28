#  https://github.com/rlxrd/aiogram_fast_pt1/blob/main/app/handlers.pyfrom
from aiogram import Bot, Dispatcher
import asyncio

from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.handlers import router
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
scheduler_ = AsyncIOScheduler()


async def main():
    scheduler_.start()

    bot_commands = [
        BotCommand(command="/start", description="Starting bot"),
        BotCommand(command="/help", description="Getting more info")
    ]
    await bot.set_my_commands(bot_commands)
    dp = Dispatcher()  # message handler
    dp.include_router(router)  # pass dp to the file where router is located

    await dp.start_polling(bot)


# The label if __name__ == "__main__" - means that main will be executed only if the file is started,
# if it is imported – it will not be started.
if __name__ == "__main__":
    try:
        print("Starting bot.....Success!")
        asyncio.run(main())
    except Exception as ex:
        print(f"There is some error: {ex}")

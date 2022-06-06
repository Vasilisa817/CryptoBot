import asyncio, aioschedule
import aioschedule as schedule
import logging

from app.config_reader import load_config
from app.handlers.common import register_handlers_common
from app.swapy import swapy_curs

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import BotCommand
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage


config = load_config("config/bot.ini")
# Объявление и инициализация объектов бота и диспетчера
bot = Bot(token=config.tg_bot.token)
dp = Dispatcher(bot, storage=MemoryStorage())

logger = logging.getLogger(__name__)
# Настройка логирования в stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger.error("Starting bot")

register_handlers_common(dp, config.tg_bot.admin_id)

class OrderCrypto(StatesGroup):
    waiting_for_summ = State()

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="btc", description="BTC"),
        BotCommand(command="eth", description="ETH"),
        BotCommand(command="usdt", description="USDT"),
        BotCommand(command="cancel", description="Отменить текущее действие")
    ]
    await bot.set_my_commands(commands)

sell_value = 0
buy_value = 0

sell_value = swapy_curs()[0]
buy_value = swapy_curs()[1]

async def update_value():
    global sell_value, buy_value
    try:
        sell_value = swapy_curs()[0]
        buy_value = swapy_curs()[1]
        print(sell_value, buy_value)
    except Exception as error:
        print(error)

async def scheduler():
    schedule.every(10).minutes.do(update_value)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())

@dp.message_handler(commands='start')
async def crypto_start(message: types.Message):
    await message.answer("Hello!")


@dp.message_handler(commands=['btc', 'eth', 'usdt'])
async def crypto_chosen(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(text=f"Продать {message.text.lower()[1:]}",
                                   callback_data=f'sell:{message.text.lower()[1:]}'),
        types.InlineKeyboardButton(text=f"Купить {message.text.lower()[1:]}",
                                   callback_data=f'buy:{message.text.lower()[1:]}'),
        types.InlineKeyboardButton(text="Связаться с менеджером",
                                   url="https://t.me/nemolyaev")
    ]
    keyboard.add(*buttons)
    kr = str(message.text[1:]).upper()
    await message.answer((f'Курс {kr}: \n продать: {sell_value[kr]} RUB\n'
    f' купить: {buy_value[kr]} RUB \nВыберите желаемую операцию'),
        reply_markup=keyboard)


@dp.callback_query_handler(text=['buy:btc', 'buy:eth', 'buy:usdt'], state=None)
async def crypto_status(callback: types.CallbackQuery, state: None):
    await state.finish()   # Заранее сбрасываем state
    crypto_name = callback.data   # вытаскиваем название крипты из колбека
    await OrderCrypto.waiting_for_summ.set()
    await state.update_data(crypto_name=crypto_name)   # Записываем в state название валюты, чтобы использовать в итоговой функции
    await callback.message.answer(f'Введите сумму в RUB для расчета покупки {crypto_name[4:].upper()}:')
    await callback.answer()

@dp.callback_query_handler(text=['sell:btc', 'sell:eth', 'sell:usdt'], state=None)
async def crypto_status(callback: types.CallbackQuery, state: None):
    await state.finish()
    crypto_name = callback.data
    await OrderCrypto.waiting_for_summ.set()
    await state.update_data(crypto_name=crypto_name)
    await callback.message.answer(f'Введите сумму {crypto_name[5:].upper()} для расчета продажи:')
    await callback.answer()


@dp.message_handler(state=OrderCrypto.waiting_for_summ)
async def crypto_result(message: types.Message, state: FSMContext):
    data = await state.get_data()
    crypto_name = data.get('crypto_name')
    await state.finish()
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add([types.InlineKeyboardButton(text="Связаться с менеджером",
                                   url="https://t.me/nemolyaev")])
    if not message.text.isdigit():
        answer_str = 'Рассчет невозможен'
    elif 'sell' in crypto_name:
        v = float(message.text)
        sell_v = float(sell_value[crypto_name[5:].upper()])
        rub_summ = '{:.2f}'.format(v * sell_v)
        answer_str = f'{message.text} x {sell_value[crypto_name[5:].upper()]} = {rub_summ} RUB'
    elif 'buy' in crypto_name:
        v = float(message.text)
        buy_v = float(buy_value[crypto_name[4:].upper()])
        rub_summ = '{:.2f}'.format(v / buy_v)
        answer_str = f'{message.text} / {buy_value[crypto_name[4:].upper()]} = {rub_summ} {crypto_name[4:].upper()}'
    else:
        answer_str = 'Рассчет невозможен'
    await message.answer(f'Расчет: {answer_str}', reply_markup=keyboard)


if __name__ == '__main__':
     executor.start_polling(dp, skip_updates=False, on_startup=on_startup)

from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiogram.utils.markdown as fmt

from app.config_reader import load_config

config = load_config("config/bot.ini")
bot = Bot(token=config.tg_bot.token)
dp = Dispatcher(bot)


price1 = {'btc':1000000, 'eth':15000, 'usdt':66.75}
price2 = {'btc':900000, 'eth':13000, 'usdt':63.75}

available_names_crypto = ["btc", "eth", "usdt"]
available_status = ["buy", "sale"]

class OrderCrypto(StatesGroup):
    #aiting_for_crypto_name = State()
    waiting_for_status = State()
    waiting_for_summ = State()


async def crypto_start(message: types.Message):
    await message.answer("Hello!")
    #await OrderCrypto.waiting_for_crypto_name.set()

async def crypto_chosen(message: types.Message):
    # проверка имени крипты
    if message.text.lower()[1:] not in available_names_crypto:
        await message.answer("Пожалуйста, выберите криптовалюту, используя меню ниже.")
    # задаем инлайн кнопки
    buttons = [
        types.InlineKeyboardButton(text=f"Продать  {message.text.lower()[1:]}", callback_data="sale"),
        types.InlineKeyboardButton(text=f"Купить { message.text.lower()[1:]}", callback_data="buy"),
        types.InlineKeyboardButton(text="Связаться с менеджером", url="https://t.me/nemolyaev")
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    # выводим сообщение с курсом и кнопками
    await message.answer(
        fmt.text(
            fmt.text(f"Продать: {message.text.lower()[1:]}"),
            fmt.text(f"1 BTC = {price1[message.text.lower()[1:]]} RUB"),
            fmt.text(" "),
            fmt.text(f"Купить {message.text.lower()[1:]}: "),
            fmt.text(f"1 BTC = {price2[message.text.lower()[1:]]} RUB"),
            fmt.text("/buy /sale"),
            sep="\n"
        ), parse_mode="HTML",
        reply_markup=keyboard
    )
    await OrderCrypto.waiting_for_status.set()

@dp.callback_query_handler(text="buy", state=OrderCrypto.waiting_for_status)
async def crypto_status(call: types.CallbackQuery, state: FSMContext):
    # chosen_status присвоили выбор операции buy или sale
    #await state.update_data(chosen_status=call.text.lower())
    await call.message.answer("Введите сумму для предварительного расчета:")
    await OrderCrypto.waiting_for_summ.set()

async def price_crypto(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректную сумму")
    await state.update_data(chosen_summ=message.text.lower())
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            text="Связаться с менеджером",
            url="https://t.me/nemolyaev"
        )
    )
    data = await state.get_data()
    if data['chosen_status']=="/buy":
        order_sum = int(data['chosen_summ']) / price2[data['chosen_crypto'][1:]]
        await message.answer(
            f"Предварительный расчет: {data['chosen_summ']} / {price2[data['chosen_crypto'][1:]]} = {order_sum} {data['chosen_crypto']}",
            reply_markup=keyboard
        )
    else:
        order_sum = int(data['chosen_summ']) * price1[data['chosen_crypto'][1:]]
        await message.answer(
            f"Предварительный расчет: {data['chosen_summ']} * {price1[data['chosen_crypto'][1:]]} = {order_sum} RUB",
            reply_markup=keyboard
        )
    
    await state.finish()


def register_handlers_crypto(dp: Dispatcher):
    dp.register_message_handler(crypto_start, commands="start", state="*")
    dp.register_message_handler(crypto_chosen, commands=["btc", "eth", "usdt"], state="*")
    #dp.register_message_handler(crypto_status, state=OrderCrypto.waiting_for_status)
    dp.register_message_handler(price_crypto, state=OrderCrypto.waiting_for_summ)

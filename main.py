import asyncio
import logging
import time
import aiogram.types
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.dispatcher import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, \
    KeyboardButton, KeyboardButtonRequestUsers, ReplyKeyboardRemove
from pytonconnect.exceptions import UserRejectsError
import config
from connector import get_connector
from price_info import price_info, rewrite_stars, rewrite_ton, rewrite_conversion_rate
from messages import get_comment_message


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
bot = Bot(config.TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.default_parse_mode = ParseMode.HTML


faq_message = '''*Как это работает и почему цена ниже?*

Бот автоматически покупает звёзды за криптовалюту по более выгодному курсу, а затем переводит их на ваш аккаунт. За эту автоматизацию мы берём небольшой процент. Звёзды поступают на ваш аккаунт (или указанный вами) в течение 5 минут и становятся доступными для использования сразу.

*Это безопасно и законно.*'''

welcome_message = '''*Мы не скам\\!*
[Кошелёк](https://tonviewer.com/EQDha1Ab1gQ4QYkBHXWUiwkWvqHIjXRCc7ZeFSy58Oes-Xpj), с которого мы оплачиваем Звёзды\\.

*Telegram Stars* 🌟 по выгодной цене\\!

Выберите количество звёзд ниже или просто отправьте цифру в чат, чтобы приобрести нужное количество'''

faq_message = faq_message.replace('!', '\\!').replace(')','\\)').replace('(', '\\(').replace('.', '\\.').replace('-', '\\-')


async def get_start_keyboard():
    start_keyboard = InlineKeyboardMarkup(inline_keyboard=[])  # 2 buttons per row

    stars_prices, ton, conversion_rate = await price_info('price_info.json')
    for stars, price in stars_prices.items():
        button_text = f"🌟{stars} Звёзд - {price}₽"
        start_keyboard.inline_keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"buy_{stars}")])
    start_keyboard.inline_keyboard.extend([[InlineKeyboardButton(text=f'🌟Ввести свой вариант (1 звезда - {conversion_rate}₽)', callback_data='buy_custom')],
                [InlineKeyboardButton(text='Отзывы📝', url='https://t.me/starsshoppin/7?comment=5'),
                 InlineKeyboardButton(text='Помощь💬', url='https://t.me/StarsShoping_bot'),
                 InlineKeyboardButton(text='ТГ Канал📣', url='https://t.me/starsshoppin')], [InlineKeyboardButton(text='Как это работает⁉️', callback_data='faq')]])
    return start_keyboard


class UserStates(StatesGroup):
    custom_amount = State()
    gift = State()
    new_prices = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    start_keyboard = await get_start_keyboard()
    await message.answer(welcome_message, reply_markup=start_keyboard, parse_mode='MarkdownV2')


async def connect_wallet(message: Message, wallet_name: str):
    connector = get_connector(message.chat.id)
    wallets_list = connector.get_wallets()
    wallet = next((w for w in wallets_list if w['name'] == wallet_name), None)

    if wallet is None:
        raise Exception(f'Unknown wallet: {wallet_name}')

    generated_url = await connector.connect(wallet)

    await message.edit_text('Подключите Wallet кнопкой ниже', reply_markup=aiogram.types.InlineKeyboardMarkup(inline_keyboard=
         [[aiogram.types.InlineKeyboardButton(text='Подключить', url=generated_url)]]))

    for _ in range(180):
        await asyncio.sleep(1)
        if connector.connected:
            await message.answer('Кошелек успешно подключен')
            return
    await message.edit_text('Превышено время ожидания подключения, повторите заново по кнопке ниже', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='Подключить Wallet', url=await connector.connect(wallet))
    ]]))


@dp.message(Command('disconnect'))
async def disconnect_handler(message: Message):
    start_keyboard = await get_start_keyboard()
    try:
        await disconnect_wallet(message)
        await message.answer('Wallet успешно отключен', reply_markup=start_keyboard)
    except Exception:
        try:
            await disconnect_wallet(message)
        except Exception as e:
            print(f"Не удалось отключить Wallet: {e}")


@dp.message(Command('edit_prices'))
async def edit_prices(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user.username or message.from_user.username != 'Aristo_TAG':
        await message.delete()
        return
    else:
        price_list= (await price_info('price_info.json'))[0]
        price_text = ', '.join([str(value) for value in price_list.values()])
        price_text = price_text.replace('.', '\\.')
        x = await message.answer(f'*Отправьте только цены, по возрастанию соответсвующих количеств*\nПример для справки, основанный на предыдущих ценах \\(Можно использовать целые числа\\)\n\n\n{price_text}', parse_mode='MarkdownV2')
        await state.update_data(message_toedit=x)
        await state.set_state(UserStates.new_prices)


@dp.message(UserStates.new_prices)
async def new_prices(message: Message, state: FSMContext):
    user_data = await state.get_data()
    message_toedit = user_data['message_toedit']
    try:
        new_price_text = ''
        price_list = (await price_info('price_info.json'))[0]
        new_price_list = message.text.split(', ')
        data = {}
        for price in new_price_list:
            i = new_price_list.index(price)
            price = float(price)
            keys = list(price_list.keys())
            amount = keys[i]
            data.update({amount: price})
            new_price_text += f'🌟{amount} Звёзд \\- {price}₽\n'
        new_price_text = new_price_text.replace('.', '\\.')
        await state.update_data(new_starprices=data)
        await message_toedit.edit_text(f'*Указанные ниже цены правильны?*\n{new_price_text}', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Да', callback_data='new_starprices_true'), InlineKeyboardButton(text='Нет', callback_data='new_starprices_false')]]), parse_mode='MarkdownV2')
        await message.delete()

    except Exception as e:
        print(e)
        price_list = (await price_info('price_info.json'))[0]
        price_text = ', '.join([str(value) for value in price_list.values()])
        price_text = price_text.replace('.', '\\.')
        await message_toedit.edit_text(f'*Пожалуйста, следуйте указанному примеру \\(Можно использовать целые числа\\)*\n\n\n{price_text}', parse_mode='MarkdownV2')
        await message.delete()


@dp.message(Command('ton'))
async def edit_ton(message: Message, state: FSMContext):
    await state.clear()

    if not message.from_user.username or message.from_user.username != 'Aristo_TAG':
        await message.delete()
        return

    parts = message.text.split()
    if len(parts) > 1:
        try:
            if parts[1] == 'current':
                ton = (await price_info('price_info.json'))[1]
                await message.answer(f'Нынешняя цена за 1 TON🪙: {ton}')
            elif isinstance(float(parts[1]), float):
                new_rate = float(parts[1])
                await rewrite_ton(new_rate)
                await message.answer(f'Цена за 1 TON🪙 успешно изменена на {parts[1]}')
            else:
                await message.answer('*Пожалуйста, используйте команду корректно*\n/ton current: Нынешняя цена за 1 TON🪙\n/ton число: задача новой цены за 1 TON🪙', parse_mode='MarkdownV2')
        except Exception as e:
            print(e)
            await message.answer('*Что\\-то пошло не так, пожалуйста, воспользуйтесь командой заново*\n/ton current: Нынешняя цена за 1 TON🪙\n/ton число: задача новой цены за 1 TON🪙', parse_mode='MarkdownV2')
    else:
        await message.answer('*Пожалуйста, используйте команду корректно*\n/ton current: Нынешняя цена за 1 TON🪙\n/ton число: задача новой цены за 1 TON🪙', parse_mode='MarkdownV2')
    await message.delete()


@dp.message(Command('starrate'))
async def edit_starrate(message: Message, state: FSMContext):
    await state.clear()

    if not message.from_user.username or message.from_user.username != 'Aristo_TAG':
        await message.delete()
        return

    parts = message.text.split()
    if len(parts) > 1:
        try:
            if parts[1] == 'current':
                rate = (await price_info('price_info.json'))[2]
                await message.answer(f'Нынешняя цена за 🌟1 звезду: {rate}')
            elif isinstance(float(parts[1]), float):
                new_rate = float(parts[1])
                await rewrite_conversion_rate(new_rate)
                await message.answer(f'Цена за 🌟1 звезду успешно изменена на {parts[1]}')
            else:
                await message.answer(
                    '*Пожалуйста, используйте команду корректно*\n/starrate current: Нынешняя цена за 🌟1 звезду\n/starrate число: задача новой цены за 🌟1 звезду',
                    parse_mode='MarkdownV2')
        except Exception as e:
            print(e)
            await message.answer(
                '*Что\\-то пошло не так, пожалуйста, воспользуйтесь командой заново*\n/starrate current: Нынешняя цена за 🌟1 звезду\n/starrate число: задача новой цены за 🌟1 звезду',
                parse_mode='MarkdownV2')
    else:
        await message.answer(
            '*Пожалуйста, используйте команду корректно*\n/starrate current: Нынешняя цена за 🌟1 звезду\n/starrate число: задача новой цены за 🌟1 звезду',
            parse_mode='MarkdownV2')
    await message.delete()


@dp.callback_query(lambda call: True)
async def callback_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    start_keyboard = await get_start_keyboard()
    data = call.data
    user_data = await state.get_data()
    if data.startswith('connect:'):
        wallet_name = data.split(':')[1]
        await connect_wallet(call.message, wallet_name)
        if 'price_ton' in user_data.keys():
            chat_id = call.from_user.id
            connector = get_connector(chat_id)
            await connector.restore_connection()
            price = user_data['price_ton']
            amount = user_data['amount']
            comment = f"🌟{amount} Звезд за {price} TON🪙"
            username = user_data['username']
            await send_transaction(call, comment, price*(10**9), connector, username, amount)
            await call.message.edit_text('Подтвердите подключение и транзакцию в приложении, после чего вам отправятся звезды в течении 15 минут', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Назад◀️', callback_data='back')]]))
            await state.clear()

    elif data == 'send_tr':
        chat_id = call.from_user.id
        connector = get_connector(chat_id)
        connected = await connector.restore_connection()
        price = user_data['price_ton']
        amount = user_data['amount']
        comment = f"🌟{amount} Звезд за {price} TON🪙"
        username = user_data['username']
        if connected:
            await send_transaction(call, comment, price*(10**9), connector, username, amount)
            await state.clear()
        else:
            wallets_list = connector.get_wallets()
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Подключить Wallet', callback_data=f"connect:{wallets_list[0]['name']}")]])
            await call.message.edit_text('Пожалуйста, подключите адрес из ниже перечисленных сервисов', reply_markup=keyboard)

    elif 'buy' in data:
        username = call.from_user.username
        if not username:
            await call.message.edit_text('К вашему акаунту не прикреплен юзернейм, для дальнейшего пользования сервисом создайте юзернейм и повторите процедуру снова', reply_markup=start_keyboard)
            return
        key = data.split('_')[1]
        if key != 'custom':
            stars_prices, ton, conversion_rate = await price_info('price_info.json')
            stars = key
            price = stars_prices.get(stars) if stars in stars_prices.keys() else user_data['price_rub']
            from yoomoney_payments import yoomoney_url, check_transaction
            rub_url, rub_label = yoomoney_url(username, call.from_user.id, price, stars)
            rub_to_ton = round(price/ton, 3)

            text = f"Вы собираетесь купить *{stars} Звезд🌟* на аккаунт @{call.from_user.username} за *{price}₽ или {rub_to_ton}TON🪙*"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Отправить другому пользователю🙋‍♂️', callback_data='gift')],
                [InlineKeyboardButton(text=f'Оплатить {price}₽💸', url=rub_url)],
                [InlineKeyboardButton(text=f"Оплатить {rub_to_ton}TON🪙", callback_data="send_tr")]
            ])
            text = text.replace('!', '\\!').replace(')','\\)').replace('(', '\\(').replace('.', '\\.').replace('-', '\\-').replace('_', '\\_')
            await call.message.edit_text(text, reply_markup=keyboard, parse_mode='MarkdownV2')
            await state.update_data(amount=stars, price_rub=price, price_ton=rub_to_ton, username=username)
            await asyncio.gather(check_transaction(rub_label, username=username, amount=stars, message=call.message, user_id=call.from_user.id))
        else:
            await call.message.edit_text('*Отправьте в чат требуемое количество Звёзд 🌟*.\n\nДля отмены воспользуйтесь кнопкой ниже'.replace('!', '\\!').replace(')','\\)').replace('(', '\\(').replace('.', '\\.').replace('-', '\\-')
                , reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Назад◀️', callback_data='back')]]), parse_mode='MarkdownV2')
            await state.update_data(call=call, username=username)
            await state.set_state(UserStates.custom_amount)

    elif data == 'gift':
        request_id = int(time.time()+call.from_user.id)//10000000

        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить контакт', request_users=KeyboardButtonRequestUsers(request_id=request_id, user_is_bot=False, request_username=True, max_quantity=1))], [KeyboardButton(text='Назад◀️')]], resize_keyboard=True)
        await state.set_state(UserStates.gift)
        message_todelete = await call.message.answer('Отправьте имя пользователя в чат либо воспользуйтесь кнопкой ниже', reply_markup=keyboard)
        await state.update_data(request_id=request_id, message_todelete=message_todelete)
        await call.message.delete()

    elif 'new_starprices' in data:
        key = data.split('_')[2]
        if key == 'true':
            new_starprices = user_data['new_starprices']
            await rewrite_stars(new_starprices)
            starts_keyboard = await get_start_keyboard()
            await call.message.edit_text('*Цены на звезды успешно изменены*', parse_mode='MarkdownV2', reply_markup=starts_keyboard)
            await state.clear()
        else:
            await call.message.edit_text('Пожалуйста, начните процесс заново с команды /edit_prices')
    elif data == 'back':
        await state.clear()
        await call.message.edit_text(welcome_message, reply_markup=start_keyboard, parse_mode='MarkdownV2')
    elif data == 'faq':
        await call.message.edit_text(faq_message, parse_mode='MarkdownV2', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Назад◀️', callback_data='back')]]))


@dp.message(UserStates.custom_amount)
async def custom_amount(message: Message, state: FSMContext):
    amount = message.text
    user_data = await state.get_data()
    username = user_data['username']
    try:
        amount = int(amount)
    except Exception as e:
        print(e)
        call = user_data['call']
        await message.delete()
        if isinstance(call, CallbackQuery):
            await call.message.edit_text('Пожалуйста, введите правильную сумму или отмените действие кнопкой ниже',
                                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                             [InlineKeyboardButton(text='Назад◀️', callback_data='back')]]))
            return
    if amount < 50:
        await message.answer('Введенная вами сумма меньше минимального порога в 50, повторите с другой суммой либо отмените действие кнопкой ниже', reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                             [InlineKeyboardButton(text='Назад◀️', callback_data='back')]]))
        await message.delete()
        return
    await state.update_data(amount=amount)
    stars_prices, ton, conversion_rate = await price_info('price_info.json')
    stars = amount
    price = round(amount * conversion_rate)
    from yoomoney_payments import yoomoney_url, check_transaction
    rub_url, rub_label = yoomoney_url(username, message.from_user.id, price, stars)
    rub_to_ton = round(price / ton, 3)

    text = f"Вы собираетесь купить *{stars} Звезд🌟* на аккаунт @{username} за *{price}₽ или {rub_to_ton}TON🪙*"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Отправить другому пользователю🙋‍♂️', callback_data='gift')],
                [InlineKeyboardButton(text=f'Оплатить {price}₽💸', url=rub_url)],
                [InlineKeyboardButton(text=f"Оплатить {rub_to_ton}TON🪙", callback_data="send_tr")]
            ])
    text = text.replace('!', '\\!').replace(')', '\\)').replace('(', '\\(').replace('.', '\\.').replace('-',
                                                                                                                '\\-').replace(
                '_', '\\_')


    await message.answer(text, reply_markup=keyboard, parse_mode='MarkdownV2')
    await state.set_state()
    await state.update_data(amount=stars, price_rub=price, price_ton=rub_to_ton, username=username)
    await asyncio.gather(check_transaction(rub_label, username, stars, message, user_id=message.from_user.id))


@dp.message(Command('give_id'))
async def give_id(message: Message):
    await message.answer(str(message.from_user.id))


@dp.message(UserStates.gift)
async def gift(message: Message, state: FSMContext):
    user_data = await state.get_data()
    message_todelete = user_data['message_todelete']

    x = await message.answer('/remove_keyboard', reply_markup=ReplyKeyboardRemove())
    await x.delete()
    if message.users_shared:
        user = message.users_shared.users[0]
        if user.username:
            stars_prices, ton, conversion_rate = await price_info('price_info.json')
            stars = user_data['amount']
            price = stars_prices.get(stars) if stars in stars_prices.keys() else user_data['price_rub']
            from yoomoney_payments import yoomoney_url, check_transaction
            rub_url, rub_label = yoomoney_url(user.username, message.from_user.id, price, stars)
            rub_to_ton = round(price / ton, 3)
            text = f"Вы собираетесь купить *{stars} Звезд🌟* на аккаунт @{user.username} за *{price}₽ или {rub_to_ton}TON🪙*"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Отправить другому пользователю🙋‍♂️', callback_data='gift')],
                [InlineKeyboardButton(text=f'Оплатить {price}₽💸', url=rub_url)],
                [InlineKeyboardButton(text=f"Оплатить {rub_to_ton}TON🪙", callback_data="send_tr")]
            ])
            text = text.replace('!', '\\!').replace(')', '\\)').replace('(', '\\(').replace('.', '\\.').replace('-','\\-').replace('_', '\\_')

            await state.update_data(username=user.username)
            await message_todelete.delete()
            await message.answer(text, reply_markup=keyboard, parse_mode='MarkdownV2')
            await asyncio.gather(check_transaction(rub_label, user.username, stars, message, user_id=message.from_user.id))
            return
        else:
            await message_todelete.delete()
            await message.answer('У пользователя не установлен username, пожалуйста, попросите их установить username и повторите попытку', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Назад◀️', callback_data='back')]]))

    else:
        if message.text == 'Назад◀️':
            start_keyboard = await get_start_keyboard()
            await message.answer(welcome_message, reply_markup=start_keyboard)
            await message_todelete.delete()
            return
        username = message.text.strip() if not message.text.strip().startswith('@') else message.text.strip().replace('@', '')
        from username_search import check_username
        if not check_username(username):
            await message_todelete.delete()
            await message.answer(f'Пользователь @{username} не найден', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Назад◀️', callback_data='back')]]))
            return
        await state.update_data(username=username)
        stars_prices, ton, conversion_rate = await price_info('price_info.json')
        stars = user_data['amount']
        price = stars_prices.get(stars) if stars in stars_prices.keys() else user_data['price_rub']
        from yoomoney_payments import yoomoney_url, check_transaction
        rub_url, rub_label = yoomoney_url(username, message.from_user.id, price, stars)
        rub_to_ton = round(price / ton, 3)

        text = f"Вы собираетесь купить *{stars} Звезд🌟* на аккаунт @{username} за *{price}₽ или {rub_to_ton}TON🪙*"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Отправить другому пользователю🙋‍♂️', callback_data='gift')],
            [InlineKeyboardButton(text=f'Оплатить {price}₽💸', url=rub_url)],
            [InlineKeyboardButton(text=f"Оплатить {rub_to_ton}TON🪙", callback_data="send_tr")]
        ])
        text = text.replace('!', '\\!').replace(')', '\\)').replace('(', '\\(').replace('.', '\\.').replace('-',
                                                                                                            '\\-').replace(
            '_', '\\_')

        await message.answer(text, reply_markup=keyboard, parse_mode='MarkdownV2')
        await asyncio.gather(check_transaction(rub_label, username, stars, message, user_id=message.from_user.id))


    await state.set_state()
    await message_todelete.delete()




async def send_transaction(call: CallbackQuery, comment, price, connector, username, amount):
    start_keyboard = await get_start_keyboard()
    transaction = {
        'valid_until': int(time.time() + 3600),
        'messages': [
            get_comment_message(
                destination_address=config.TONKEEPER_ADDRESS,
                amount=int(price),
                comment=comment
            )
        ]
    }

    try:
        await call.message.edit_text('Подтвердите транзакцию в мобильном приложении вашего кошелька')
        await asyncio.wait_for(connector.send_transaction(transaction=transaction), 300)
        from fragment_payments import proceed_request
        await asyncio.gather(proceed_request(username, amount, user_id=call.from_user.id))
    except asyncio.TimeoutError:
        await call.message.edit_text(f'*Время ожидания транзакции истекло, повторите процес заново*\n{welcome_message}', reply_markup=start_keyboard, parse_mode='MarkdownV2')
    except UserRejectsError:
        await call.message.edit_text(f'*Транзакция успешно прервана Вами\\!*\n{welcome_message}', reply_markup=start_keyboard, parse_mode='MarkdownV2')
    except Exception as e:
        await call.message.edit_text(f'Error: {e}')


async def disconnect_wallet(message: Message):
    start_keyboard = await get_start_keyboard()
    connector = get_connector(message.chat.id)
    await connector.restore_connection()

    if not connector.connected:
        await message.answer('Wallet не подключен', reply_markup=start_keyboard)
        return

    await connector.disconnect()
    await message.answer('Wallet успешно отключен', reply_markup=start_keyboard)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

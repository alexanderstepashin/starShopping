from yoomoney import Quickpay, Client
import time
from config import YOOTOKEN as yoomoney_token
import asyncio
from aiogram.types import Message
from fragment_payments import proceed_request
from main import get_start_keyboard


def yoomoney_url(username: str, user_id: int, amount: float or int, sum: float or int):
    username = username.replace('@', '')
    label = f"{username}_{round(time.time())}"
    quickpay = Quickpay(
                receiver="4100118169570055",
                quickpay_form='shop',
                targets=f"🌟{sum} Звезд",
                paymentType="SB",
                sum=amount,
                label=label,
                formcomment=f"🌟{sum} Звезд от StarShoppin",
                comment=f"🌟{sum} Звезд от StarShoppin: {user_id}_{username}"
                )

    return quickpay.redirected_url, label


async def check_transaction(label, username, amount, message: Message, user_id):
    client = Client(yoomoney_token)
    history = client.operation_history(label=label)
    operations = history.operations
    while len(operations) == 0:
        await asyncio.sleep(5)
        client = Client(yoomoney_token)
        history = client.operation_history(label=label)
        operations = history.operations
    for operation in operations:
        print(operation.status)
        status = operation.status
        start_time = time.time()
        while not operation or status != 'success':
            await asyncio.sleep(5)
            update = client.operation_details(operation.operation_id)
            status = update.status

            if time.time() - start_time > 3600:
                start_keyboard = await get_start_keyboard()
                await message.edit_text('Превышен таймаут платежа, пожалуйста, повторите заново', reply_markup=start_keyboard)
                return

    await asyncio.gather(proceed_request(username, amount, user_id))

from base64 import urlsafe_b64encode
from pytoniq_core import begin_cell


def get_comment_message(destination_address: str, amount: int, comment: str) -> dict:
    return {
        'address': destination_address,
        'amount': str(amount),
        'payload': urlsafe_b64encode(
            begin_cell()
            .store_uint(0, 32)  # op code for comment message
            .store_string(comment)
            .end_cell()
            .to_boc()
        ).decode()
    }

from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def encode_qr_png(payload: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    output = BytesIO()
    qr.make_image(fill_color="black", back_color="white").get_image().save(
        output, format="PNG"
    )
    return output.getvalue()

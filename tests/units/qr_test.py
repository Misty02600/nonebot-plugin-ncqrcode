def test_qr_encoder_returns_png():
    from nonebot_plugin_ncqrcode.qr import encode_qr_png

    assert encode_qr_png("test").startswith(b"\x89PNG\r\n\x1a\n")

from nonebug import App


def test_plugin_loads(app: App):
    from nonebot_plugin_ncqrcode import __plugin_meta__
    from nonebot_plugin_ncqrcode.handlers import config, nc_command

    assert __plugin_meta__.name == "Napcat QRCode"
    assert __plugin_meta__.supported_adapters
    assert config.ncqrcode_max_qr_notifications == 3
    assert nc_command is not None

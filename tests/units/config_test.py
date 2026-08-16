def test_config_can_be_instantiated():
    from nonebot_plugin_ncqrcode.config import Config

    assert Config().model_dump() == {}

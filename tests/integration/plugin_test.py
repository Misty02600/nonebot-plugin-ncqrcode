from pathlib import Path

import pytest
from nonebug import App
from tests.units.fake import fake_group_message_event_v11


def test_plugin_metadata(app: App):
    import nonebot_plugin_ncqrcode
    from nonebot_plugin_ncqrcode import __plugin_meta__
    from nonebot_plugin_ncqrcode.config import Config
    from nonebot_plugin_ncqrcode.handlers import (
        plugin_config,
        template_demo,
    )

    assert __plugin_meta__.name == "名称"
    assert __plugin_meta__.description == "描述"
    assert __plugin_meta__.type == "application"
    assert nonebot_plugin_ncqrcode.__file__ is not None
    expected_package = (
        Path(__file__).parents[2] / "src" / "nonebot_plugin_ncqrcode" / "__init__.py"
    )
    assert Path(nonebot_plugin_ncqrcode.__file__).resolve() == expected_package.resolve()
    assert isinstance(plugin_config, Config)
    assert template_demo is not None


@pytest.mark.asyncio
async def test_template_demo_command_without_text(app: App):
    from nonebot.adapters.onebot.v11 import Message

    from nonebot_plugin_ncqrcode.handlers import template_demo

    async with app.test_matcher(template_demo) as ctx:
        bot = ctx.create_bot()
        event = fake_group_message_event_v11(
            message=Message("模板测试"),
            raw_message="模板测试",
        )
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "模板插件已加载", result=None)
        ctx.should_finished(template_demo)


@pytest.mark.asyncio
async def test_template_demo_command_with_text(app: App):
    from nonebot.adapters.onebot.v11 import Message

    from nonebot_plugin_ncqrcode.handlers import template_demo

    async with app.test_matcher(template_demo) as ctx:
        bot = ctx.create_bot()
        event = fake_group_message_event_v11(
            message=Message("模板测试 hello"),
            raw_message="模板测试 hello",
        )
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "收到参数：hello", result=None)
        ctx.should_finished(template_demo)

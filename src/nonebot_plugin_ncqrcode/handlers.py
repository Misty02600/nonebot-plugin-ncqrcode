from nonebot import get_plugin_config, on_command
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from .config import Config

plugin_config = get_plugin_config(Config)

template_demo = on_command("模板测试", aliases={"template"}, block=True)


@template_demo.handle()
async def handle_template_demo(matcher: Matcher, arg: Message = CommandArg()):
    text = arg.extract_plain_text().strip()
    if text:
        await matcher.finish(f"收到参数：{text}")

    await matcher.finish("模板插件已加载")

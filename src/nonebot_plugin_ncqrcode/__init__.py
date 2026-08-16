# from nonebot import logger, require
from nonebot.plugin import PluginMetadata  # , inherit_supported_adapters

# require("nonebot_plugin_uninfo")
# require("nonebot_plugin_alconna")
# require("nonebot_plugin_localstore")
# require("nonebot_plugin_apscheduler")
from .config import Config

__all__ = ["__plugin_meta__", "handlers"]

__plugin_meta__ = PluginMetadata(
    name="名称",
    description="描述",
    usage="模板测试 [文本]",
    type="application",  # application: 功能性插件 | library: 库插件
    homepage="https://github.com/Misty02600/nonebot-plugin-ncqrcode",
    config=Config,
    # supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    supported_adapters={"~onebot.v11"},
    extra={"author": "Misty02600"},
)

from . import handlers

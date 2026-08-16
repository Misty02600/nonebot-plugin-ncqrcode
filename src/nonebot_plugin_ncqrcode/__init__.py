from __future__ import annotations

from nonebot import require
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_alconna")
require("nonebot_plugin_uninfo")
require("nonebot_plugin_localstore")

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="Napcat QRCode",
    description="监控 NapCat 登录状态，并推送离线通知与二维码",
    usage="/nc subscribe | unsubscribe | qrcode",
    type="application",
    homepage="https://github.com/Misty02600/nonebot-plugin-ncqrcode",
    config=Config,
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna",
        "nonebot_plugin_uninfo",
    ),
    extra={"author": "Misty02600 <xiao02600@gmail.com>"},
)

from . import handlers as _handlers  # noqa: F401

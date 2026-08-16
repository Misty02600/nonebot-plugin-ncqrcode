from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import monotonic

from nonebot import get_driver, get_plugin_config, logger
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import (
    Alconna,
    Args,
    Image,
    Match,
    Text,
    UniMessage,
    on_alconna,
)
from nonebot_plugin_localstore import get_plugin_data_file
from nonebot_plugin_uninfo import Uninfo
from nonebot_plugin_uninfo.target import to_target

from .client import LoginStatus, NapCatClient, NapCatError
from .config import Config
from .qr import encode_qr_png
from .store import TargetStore

CHECK_INTERVAL = 30.0
FAILURE_THRESHOLD = 2
QR_REFRESH_INTERVAL = 110.0
AUTO_REFRESH_ATTEMPTS = 3
RESTART_GRACE = 15.0
RECOVERY_TIMEOUT = 60.0


class _StaleQRCodeError(NapCatError):
    pass


@dataclass(slots=True)
class _Incident:
    active: bool = False
    failures: int = 0
    restart_attempted: bool = False
    last_qr_attempt: float = 0.0
    last_qr: str | None = None
    qr_count: int = 0

    def reset(self) -> None:
        self.active = False
        self.failures = 0
        self.restart_attempted = False
        self.last_qr_attempt = 0.0
        self.last_qr = None
        self.qr_count = 0


@dataclass(frozen=True, slots=True)
class _RecoveryResult:
    status: LoginStatus
    restarted: bool = False
    qrcode: str | None = None
    error: str | None = None


config = get_plugin_config(Config)
target_store = TargetStore(get_plugin_data_file("target.json"))
incident = _Incident()
operation_lock = asyncio.Lock()
monitor_task: asyncio.Task[None] | None = None

if config.configured:
    assert config.ncqrcode_base_url is not None
    assert config.ncqrcode_token is not None
    assert config.ncqrcode_account_id is not None
    client: NapCatClient | None = NapCatClient(
        str(config.ncqrcode_base_url),
        config.ncqrcode_token.get_secret_value(),
    )
    account_id = config.ncqrcode_account_id
else:
    client = None
    account_id = None


nc_command = on_alconna(
    Alconna("nc", Args["action?", str]),
    permission=SUPERUSER,
    use_cmd_start=True,
    block=True,
)


@nc_command.handle()
async def handle_nc_command(session: Uninfo, action: Match[str]) -> None:
    command = action.result.casefold() if action.available else "help"
    try:
        if command == "subscribe":
            message = await _subscribe(session)
        elif command == "unsubscribe":
            removed = await target_store.clear()
            message = UniMessage("已取消订阅" if removed else "当前没有订阅")
        elif command in {"qrcode", "qr"}:
            message = await _manual_qrcode()
        else:
            message = UniMessage("用法：/nc subscribe | unsubscribe | qrcode")
    except (NapCatError, OSError, TypeError, ValueError) as exc:
        message = UniMessage(str(exc))
    await message.finish()


async def _subscribe(session: Uninfo) -> UniMessage:
    _require_client()
    target = to_target(session)
    if target.self_id == account_id:
        return UniMessage("不能使用被监控的 QQ 账号接收离线通知")
    await target_store.save(target)
    return UniMessage("订阅成功；后续通知将发送到当前会话")


async def _manual_qrcode() -> UniMessage:
    current_client = _require_client()
    async with operation_lock:
        status = await current_client.status()
        if status.online:
            return UniMessage(f"QQ {account_id} 当前在线，无需扫码")

        incident.active = True
        incident.failures = max(incident.failures, FAILURE_THRESHOLD)
        result = await _recover(status, explicit=True)
        if result.status.online:
            incident.reset()
            return UniMessage(f"QQ {account_id} 已恢复在线")
        if result.error:
            return UniMessage(f"QQ {account_id} 获取二维码失败：{result.error}")
        if not result.qrcode:
            return UniMessage(f"QQ {account_id} 尚未生成二维码")

        incident.last_qr = result.qrcode
        incident.last_qr_attempt = monotonic()
        action = "已重启 NapCat，并生成" if result.restarted else "已生成"
        return UniMessage(
            [
                Text(f"QQ {account_id} {action}新的登录二维码："),
                Image(raw=encode_qr_png(result.qrcode), name="napcat-login.png"),
            ]
        )


async def _monitor() -> None:
    while True:
        try:
            await _check_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Napcat QRCode 监控失败")
        await asyncio.sleep(CHECK_INTERVAL)


async def _check_once() -> None:
    current_client = _require_client()
    async with operation_lock:
        try:
            status = await current_client.status()
        except NapCatError as exc:
            incident.failures += 1
            if not incident.active and incident.failures >= FAILURE_THRESHOLD:
                incident.active = True
                await _notify_text(f"{_prefix()} WebUI 无法访问：{exc}")
            return

        if status.online:
            if incident.active:
                await _notify_text(f"{_prefix()} 已恢复在线")
            incident.reset()
            return

        incident.failures += 1
        if not incident.active:
            if incident.failures < FAILURE_THRESHOLD:
                return
            incident.active = True
            await _notify_text(f"{_prefix()} 已离线，正在获取登录二维码")

        now = monotonic()
        if incident.qr_count >= config.ncqrcode_max_qr_notifications:
            return
        if now - incident.last_qr_attempt < QR_REFRESH_INTERVAL:
            return

        incident.last_qr_attempt = now
        result = await _recover(status, explicit=False)
        if result.status.online:
            await _notify_text(f"{_prefix()} 已恢复在线")
            incident.reset()
        elif result.error:
            await _notify_text(f"{_prefix()} 获取二维码失败：{result.error}")
        elif result.qrcode and result.qrcode != incident.last_qr:
            incident.last_qr = result.qrcode
            incident.qr_count += 1
            await _notify_qrcode(result.qrcode)


async def _recover(status: LoginStatus, *, explicit: bool) -> _RecoveryResult:
    previous_qr = status.qrcode
    restarted = False
    try:
        if status.offline and (explicit or not incident.restart_attempted):
            status = await _restart()
            restarted = True
            if status.online:
                return _RecoveryResult(status, restarted=True)
            if status.offline:
                raise NapCatError("NapCat 重启后 QQ 仍处于离线状态")
            qrcode = await _fresh_qrcode(
                previous_qr,
                refresh=False,
                initial=status.qrcode,
            )
        else:
            try:
                qrcode = await _refresh_qrcode(
                    previous_qr,
                    attempts=1 if explicit else AUTO_REFRESH_ATTEMPTS,
                )
            except _StaleQRCodeError as exc:
                if incident.restart_attempted and not explicit:
                    raise
                status = await _restart()
                restarted = True
                if status.online:
                    return _RecoveryResult(status, restarted=True)
                if status.offline:
                    raise NapCatError("NapCat 重启后 QQ 仍处于离线状态") from exc
                qrcode = await _fresh_qrcode(
                    previous_qr,
                    refresh=False,
                    initial=status.qrcode,
                )
        return _RecoveryResult(status, restarted=restarted, qrcode=qrcode)
    except (NapCatError, OSError, ValueError) as exc:
        return _RecoveryResult(status, restarted=restarted, error=str(exc))


async def _refresh_qrcode(previous: str | None, *, attempts: int) -> str:
    last_error: _StaleQRCodeError | None = None
    for _ in range(attempts):
        try:
            return await _fresh_qrcode(previous, refresh=True)
        except _StaleQRCodeError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


async def _restart() -> LoginStatus:
    current_client = _require_client()
    incident.restart_attempted = True
    await current_client.restart()
    await asyncio.sleep(RESTART_GRACE)
    deadline = monotonic() + RECOVERY_TIMEOUT
    status = await current_client.status()
    while monotonic() < deadline:
        if status.online or not status.offline:
            return status
        await asyncio.sleep(2)
        status = await current_client.status()
    return status


async def _fresh_qrcode(
    previous: str | None,
    *,
    refresh: bool,
    initial: str | None = None,
) -> str:
    current_client = _require_client()
    saw_old = initial is not None and initial == previous
    try:
        async with asyncio.timeout(15):
            if refresh:
                await current_client.refresh_qrcode()
            if initial and initial != previous:
                return initial
            while True:
                await asyncio.sleep(1)
                qrcode = await current_client.qrcode()
                if previous is None or qrcode != previous:
                    return qrcode
                saw_old = True
    except TimeoutError as exc:
        if saw_old:
            raise _StaleQRCodeError("NapCat 仍返回旧二维码") from exc
        raise NapCatError("NapCat 未在 15 秒内生成二维码") from exc


async def _notify_text(text: str) -> None:
    await _notify(UniMessage(text))


async def _notify_qrcode(qrcode: str) -> None:
    await _notify(
        UniMessage(
            [
                Text(f"{_prefix()} 需要扫码登录："),
                Image(raw=encode_qr_png(qrcode), name="napcat-login.png"),
            ]
        )
    )


async def _notify(message: UniMessage) -> None:
    try:
        target = await target_store.load()
        if target is None:
            logger.warning("Napcat QRCode 尚未设置通知目标")
            return
        await message.send(target=target)
    except Exception:
        logger.exception("Napcat QRCode 通知发送失败")


def _require_client() -> NapCatClient:
    if client is None:
        raise ValueError("尚未配置 NapCat 地址、密钥和 QQ 号")
    return client


def _prefix() -> str:
    return f"[NapCat] QQ {account_id}"


driver = get_driver()


@driver.on_startup
async def start_monitoring() -> None:
    global monitor_task
    if client is None:
        logger.warning("Napcat QRCode 未配置，后台监控不会启动")
        return
    if monitor_task is None or monitor_task.done():
        monitor_task = asyncio.create_task(_monitor(), name="ncqrcode")


@driver.on_shutdown
async def stop_monitoring() -> None:
    global monitor_task
    if monitor_task:
        monitor_task.cancel()
        await asyncio.gather(monitor_task, return_exceptions=True)
        monitor_task = None
    if client:
        await client.close()

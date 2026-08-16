from __future__ import annotations

import hashlib
from dataclasses import dataclass
from time import monotonic
from typing import Any

import httpx


class NapCatError(RuntimeError):
    pass


class _Unauthorized(NapCatError):
    pass


@dataclass(frozen=True, slots=True)
class LoginStatus:
    online: bool
    offline: bool
    qrcode: str | None = None


class NapCatClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._token = token
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=10)
        self._credential: str | None = None
        self._credential_expires_at = 0.0

    async def close(self) -> None:
        await self._client.aclose()

    async def status(self) -> LoginStatus:
        data = await self._post("/api/QQLogin/CheckLoginStatus")
        if not isinstance(data, dict):
            raise NapCatError("CheckLoginStatus 返回了无效数据")
        is_login = bool(data.get("isLogin"))
        is_offline = bool(data.get("isOffline"))
        return LoginStatus(
            online=is_login and not is_offline,
            offline=is_offline,
            qrcode=_optional_text(data.get("qrcodeurl")),
        )

    async def refresh_qrcode(self) -> None:
        await self._post("/api/QQLogin/RefreshQRcode")

    async def qrcode(self) -> str:
        data = await self._post("/api/QQLogin/GetQQLoginQrcode")
        if not isinstance(data, dict) or not data.get("qrcode"):
            raise NapCatError("NapCat 未返回二维码")
        return str(data["qrcode"])

    async def restart(self) -> None:
        await self._post("/api/QQLogin/RestartNapCat", allow_disconnect=True)

    async def _post(self, path: str, *, allow_disconnect: bool = False) -> Any:
        for attempt in range(2):
            credential = await self._login(force=attempt > 0)
            try:
                response = await self._client.post(
                    path,
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except (httpx.RemoteProtocolError, httpx.ReadError) as exc:
                if allow_disconnect:
                    return None
                raise NapCatError(f"NapCat WebUI 请求失败: {exc}") from exc
            except httpx.HTTPError as exc:
                raise NapCatError(f"NapCat WebUI 请求失败: {exc}") from exc

            try:
                return _decode(response)
            except _Unauthorized:
                self._credential = None
                if attempt:
                    raise
        raise _Unauthorized("NapCat WebUI 鉴权失败")

    async def _login(self, *, force: bool = False) -> str:
        if not force and self._credential and monotonic() < self._credential_expires_at:
            return self._credential

        digest = hashlib.sha256(f"{self._token}.napcat".encode()).hexdigest()
        try:
            response = await self._client.post("/api/auth/login", json={"hash": digest})
        except httpx.HTTPError as exc:
            raise NapCatError(f"无法连接 NapCat WebUI: {exc}") from exc
        data = _decode(response)
        if not isinstance(data, dict) or not data.get("Credential"):
            raise _Unauthorized("NapCat WebUI 未返回 Credential")
        self._credential = str(data["Credential"])
        self._credential_expires_at = monotonic() + 3300
        return self._credential


def _decode(response: httpx.Response) -> Any:
    if response.status_code == 401:
        raise _Unauthorized("Unauthorized")
    try:
        payload = response.json()
    except ValueError as exc:
        raise NapCatError("NapCat WebUI 返回非 JSON 数据") from exc
    if not isinstance(payload, dict):
        raise NapCatError("NapCat WebUI 返回格式无效")
    message = str(payload.get("message") or payload.get("wording") or "")
    if response.is_error or payload.get("code") != 0:
        if message.casefold() == "unauthorized":
            raise _Unauthorized(message)
        raise NapCatError(message or f"NapCat WebUI API 错误: {payload.get('code')}")
    return payload.get("data")


def _optional_text(value: Any) -> str | None:
    return None if value is None or value == "" else str(value)

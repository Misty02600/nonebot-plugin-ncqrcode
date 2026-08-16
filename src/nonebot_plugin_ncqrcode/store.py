from __future__ import annotations

import asyncio
import json
from enum import Enum
from pathlib import Path
from typing import Any

from nonebot_plugin_alconna import Target


class TargetStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()

    async def load(self) -> Target | None:
        async with self._lock:
            if not self._path.exists():
                return None
            text = await asyncio.to_thread(
                self._path.read_text,
                encoding="utf-8",
            )
        return Target.load(json.loads(text))

    async def save(self, target: Target) -> None:
        data = json.dumps(target.dump(), ensure_ascii=False, default=_json_default)
        temporary = self._path.with_suffix(".tmp")
        async with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(temporary.write_text, data, encoding="utf-8")
            await asyncio.to_thread(temporary.replace, self._path)

    async def clear(self) -> bool:
        async with self._lock:
            if not self._path.exists():
                return False
            await asyncio.to_thread(self._path.unlink)
            return True


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, set | tuple):
        return list(value)
    return str(value)

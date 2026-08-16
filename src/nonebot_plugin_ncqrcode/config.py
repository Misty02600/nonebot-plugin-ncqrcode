from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    SecretStr,
    field_validator,
    model_validator,
)


class Config(BaseModel):
    ncqrcode_base_url: HttpUrl | None = None
    ncqrcode_token: SecretStr | None = None
    ncqrcode_account_id: str | None = None
    ncqrcode_max_qr_notifications: int = Field(default=5, ge=1)

    @field_validator("ncqrcode_account_id", mode="before")
    @classmethod
    def validate_account_id(cls, value: object) -> str | None:
        if value is None:
            return None
        account_id = str(value).strip()
        if not account_id.isdigit():
            raise ValueError("ncqrcode_account_id 必须是 QQ 号")
        return account_id

    @model_validator(mode="after")
    def require_complete_connection(self) -> Config:
        values = (
            self.ncqrcode_base_url,
            self.ncqrcode_token,
            self.ncqrcode_account_id,
        )
        if any(value is not None for value in values) and not all(
            value is not None for value in values
        ):
            raise ValueError("NapCat 连接配置必须同时填写地址、密钥和 QQ 号")
        return self

    @property
    def configured(self) -> bool:
        return self.ncqrcode_base_url is not None

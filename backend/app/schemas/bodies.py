from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginTotpConfirm(BaseModel):
    pre_auth_token: str
    totp_code: str = Field(min_length=6, max_length=8)


class TotpEnableRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class TotpDisableRequest(BaseModel):
    password: str
    totp_code: str = Field(min_length=6, max_length=8)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=64)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=64)
    nickname: str = Field(default="", max_length=64)
    role_ids: list[int] = Field(default_factory=list)
    totp_required: bool = False


class UserUpdate(BaseModel):
    nickname: str = Field(default="", max_length=64)
    status: Literal["active", "disabled"] = "active"
    role_ids: list[int] = Field(default_factory=list)
    totp_required: bool = False


class StatusUpdate(BaseModel):
    status: Literal["active", "disabled"]


class ResetPassword(BaseModel):
    password: str = Field(min_length=6, max_length=64)


class RoleWrite(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    remark: str = Field(default="", max_length=255)


class RoleMenusUpdate(BaseModel):
    menu_ids: list[int] = Field(default_factory=list)


class ScheduledJobCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    job_key: str = Field(min_length=1, max_length=64)
    trigger_type: Literal["interval", "cron"]
    trigger_config: str = Field(default="{}", max_length=255)
    params: str = Field(default="{}", max_length=512)
    enabled: bool = True
    remark: str = Field(default="", max_length=255)


class ScheduledJobUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    trigger_type: Literal["interval", "cron"]
    trigger_config: str = Field(default="{}", max_length=255)
    params: str = Field(default="{}", max_length=512)
    enabled: bool = True
    remark: str = Field(default="", max_length=255)


class EnabledUpdate(BaseModel):
    enabled: bool


class JobLogCleanup(BaseModel):
    days: int | None = Field(default=None, ge=1, le=3650)


class MenuWrite(BaseModel):
    parent_id: int | None = None
    name: str = Field(min_length=1, max_length=64)
    menu_type: Literal["directory", "menu", "button"]
    path: str = Field(default="", max_length=128)
    component: str = Field(default="", max_length=128)
    permission: str = Field(default="", max_length=128)
    icon: str = Field(default="", max_length=64)
    sort: int = 0
    visible: bool = True
    status: Literal["active", "disabled"] = "active"

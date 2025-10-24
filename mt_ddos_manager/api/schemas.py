"""
Pydantic schemas for API validation
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RouterBase(BaseModel):
    name: str
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool = False
    enabled: bool = True
    tags: Optional[str] = None


class RouterCreate(RouterBase):
    pass


class RouterUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_ssl: Optional[bool] = None
    enabled: Optional[bool] = None
    tags: Optional[str] = None


class RouterResponse(RouterBase):
    id: int
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class RouterConfigBase(BaseModel):
    poll_interval: Optional[int] = None
    conn_attack_threshold: Optional[int] = None
    new_conn_rate_threshold: Optional[int] = None
    per_src_new_conn_limit: Optional[int] = None
    per_src_window: Optional[int] = None
    tighten_cooldown: Optional[int] = None
    tighten_limits: Optional[str] = None  # JSON
    restore_limits: Optional[str] = None  # JSON
    notification_prefs: Optional[str] = None  # JSON


class RouterConfigUpdate(RouterConfigBase):
    pass


class UserBase(BaseModel):
    username: str
    role: str = 'viewer'


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class EventResponse(BaseModel):
    id: int
    router_id: Optional[int] = None
    type: Optional[str] = None
    detail: Optional[str] = None
    meta: Optional[dict] = None
    created_at: datetime
    severity: Optional[str] = None


class MetricResponse(BaseModel):
    ts: datetime
    total_connections: Optional[int] = None
    new_connections: Optional[int] = None
    packets_in: Optional[int] = None
    packets_out: Optional[int] = None
    bytes_in: Optional[int] = None
    bytes_out: Optional[int] = None


class AddressListCreate(BaseModel):
    list_name: str
    address: str
    timeout: Optional[str] = None


class ActionHistoryResponse(BaseModel):
    id: int
    router_id: Optional[int] = None
    action: Optional[str] = None
    initiated_by: Optional[int] = None
    detail: Optional[str] = None
    created_at: datetime


class GlobalActionRequest(BaseModel):
    router_ids: List[int]
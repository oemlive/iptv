from typing import Optional
from pydantic import BaseModel, Field

class Source(BaseModel):
    id: str
    name: str
    url: str
    group: str = "其他"
    subgroup: str = "其他"
    provider: str = "manual"
    origin: str = "manual"
    selected: bool = False
    valid: Optional[bool] = None
    status: str = "未验证"
    width: Optional[int] = None
    height: Optional[int] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    bitrate: Optional[int] = None
    latency_ms: Optional[int] = None
    first_frame_ms: Optional[int] = None
    score: Optional[int] = None
    stability: Optional[int] = None
    last_error: Optional[str] = None
    discovered_at: Optional[str] = None
    checked_at: Optional[str] = None

class ValidateRequest(BaseModel):
    ids: list[str] = Field(default_factory=list)

class SearchRequest(BaseModel):
    providers: list[str] = ["github", "gitee"]
    queries: list[str] = ["iptv m3u", "直播源 m3u", "tv.m3u"]

class ExportRequest(BaseModel):
    ids: list[str]
    formats: list[str] = ["txt", "m3u"]
    publish: bool = True

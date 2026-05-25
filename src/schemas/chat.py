from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ResolvedProfile(BaseModel):
    profile_id: str
    name: str
    display_name: str | None = None
    gateway_port: int | None = None
    base_url: str | None = None
    status: str
    healthy: bool


class ChatModel(BaseModel):
    id: str
    label: str
    provider: str | None = None
    base_url: str | None = None
    source: str = "gateway"
    is_current: bool = False


class ChatModelListResponse(BaseModel):
    profile_id: str
    models: list[ChatModel]
    status: str | None = None
    raw: dict[str, Any] | None = None


class ProfileChatModelConfig(BaseModel):
    profile_id: str
    provider: str
    model_id: str
    model_label: str | None = None
    base_url: str | None = None
    updated_at: str


class SetProfileChatModelConfigPayload(BaseModel):
    provider: str = "auto"
    model_id: str
    model_label: str | None = None
    base_url: str | None = None


class WorkspaceChatMessage(BaseModel):
    role: str
    content: str


class WorkspaceChatSendPayload(BaseModel):
    workspace_id: str
    session_id: str
    stream_id: str | None = None
    model: str | None = None
    messages: list[WorkspaceChatMessage]
    attachments: list[str] = Field(default_factory=list)
    stream: bool = True


class WorkspaceChatStreamScope(BaseModel):
    stream_id: str
    profile_id: str
    workspace_id: str
    session_id: str


class WorkspaceChatChunkEvent(WorkspaceChatStreamScope):
    content: str


class WorkspaceChatToolProgressEvent(WorkspaceChatStreamScope):
    name: str
    label: str | None = None


class WorkspaceChatUsageEvent(WorkspaceChatStreamScope):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class WorkspaceChatDoneEvent(WorkspaceChatStreamScope):
    resolved_session_id: str | None = None


class WorkspaceChatSessionMessage(BaseModel):
    id: int
    role: str
    content: str
    timestamp: int


class WorkspaceChatSessionMessagesResponse(BaseModel):
    messages: list[WorkspaceChatSessionMessage]


class WorkspaceChatErrorEvent(WorkspaceChatStreamScope):
    message: str
    details: dict[str, Any] | None = None


class WorkspaceChatSendResponse(BaseModel):
    stream_id: str


class WorkspaceChatAbortResponse(BaseModel):
    ok: bool = True

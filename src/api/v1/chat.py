from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db_session
from db.repositories.chat_attachment_repo import ChatAttachmentRepository
from db.repositories.chat_settings_repo import ChatSettingsRepository
from db.repositories.profile_repo import ProfileRepository
from db.repositories.v12_repos import WorkspaceRepository
from schemas.chat import (
    ChatModelListResponse,
    ProfileChatModelConfig,
    ResolvedProfile,
    SetProfileChatModelConfigPayload,
    WorkspaceChatAbortResponse,
    WorkspaceChatSendPayload,
    WorkspaceChatSessionMessagesResponse,
)
from services.chat_model_service import ChatModelService
from services.chat_session_service import ChatSessionService
from services.chat_stream_service import ChatStreamService, abort_stream
from services.profile_ref_resolver import ProfileRefResolver
from services.sse_helpers import stream_sse_headers

router = APIRouter(tags=["chat"])


def _chat_model_service(session: AsyncSession = Depends(get_db_session)) -> ChatModelService:
    return ChatModelService(ProfileRepository(session), ChatSettingsRepository(session))


def _chat_stream_service(session: AsyncSession = Depends(get_db_session)) -> ChatStreamService:
    return ChatStreamService(
        ProfileRepository(session),
        ChatSettingsRepository(session),
        ChatAttachmentRepository(session),
        WorkspaceRepository(session),
    )


@router.get("/profiles/resolve", response_model=ResolvedProfile)
async def resolve_profile(
    ref: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_db_session),
) -> ResolvedProfile:
    resolver = ProfileRefResolver(ProfileRepository(session))
    return await resolver.resolve(ref)


@router.get(
    "/profiles/{profile_id}/sessions/{session_id}/messages",
    response_model=WorkspaceChatSessionMessagesResponse,
)
async def list_session_messages(
    profile_id: str,
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceChatSessionMessagesResponse:
    svc = ChatSessionService(ProfileRepository(session))
    return await svc.list_messages(profile_id, session_id)


@router.get("/profiles/{profile_id}/chat/models", response_model=ChatModelListResponse)
async def list_chat_models(
    profile_id: str,
    svc: ChatModelService = Depends(_chat_model_service),
) -> ChatModelListResponse:
    return await svc.list_models(profile_id)


@router.get("/profiles/{profile_id}/chat/model-config", response_model=ProfileChatModelConfig | None)
async def get_chat_model_config(
    profile_id: str,
    svc: ChatModelService = Depends(_chat_model_service),
) -> ProfileChatModelConfig | None:
    return await svc.get_model_config(profile_id)


@router.put("/profiles/{profile_id}/chat/model-config", response_model=ProfileChatModelConfig)
async def set_chat_model_config(
    profile_id: str,
    body: SetProfileChatModelConfigPayload,
    svc: ChatModelService = Depends(_chat_model_service),
) -> ProfileChatModelConfig:
    return await svc.set_model_config(profile_id, body)


@router.post("/profiles/{profile_id}/chat/completions")
async def chat_completions(
    profile_id: str,
    body: WorkspaceChatSendPayload,
    svc: ChatStreamService = Depends(_chat_stream_service),
):
    async def event_generator():
        async for chunk in svc.stream_chat(profile_id, body):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=stream_sse_headers(),
    )


@router.post(
    "/profiles/{profile_id}/chat/abort",
    response_model=WorkspaceChatAbortResponse,
)
async def abort_chat_stream(
    profile_id: str,
    stream_id: str = Query(..., min_length=1),
) -> WorkspaceChatAbortResponse:
    _ = profile_id
    abort_stream(stream_id)
    return WorkspaceChatAbortResponse(ok=True)

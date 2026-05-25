from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.chat_settings import ProfileChatSettings


class ChatSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, profile_id: str) -> ProfileChatSettings | None:
        return await self._session.get(ProfileChatSettings, profile_id)

    async def upsert(self, row: ProfileChatSettings) -> ProfileChatSettings:
        existing = await self.get(row.profile_id)
        if existing is None:
            self._session.add(row)
        else:
            existing.provider = row.provider
            existing.model_id = row.model_id
            existing.model_label = row.model_label
            existing.base_url = row.base_url
            existing.is_default = row.is_default
            existing.updated_at = row.updated_at
        await self._session.flush()
        return row if existing is None else existing

    async def delete(self, profile_id: str) -> None:
        row = await self.get(profile_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()

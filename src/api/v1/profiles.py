from __future__ import annotations

from fastapi import APIRouter, Depends, status

from api.deps import get_gateway_supervisor, get_profile_service
from schemas.profile import (
    ProfileCreate,
    ProfileResponse,
    ProfileStatusResponse,
    ProfileUpdate,
)
from services.gateway_supervisor import GatewaySupervisor
from services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=list[ProfileResponse])
async def list_profiles(svc: ProfileService = Depends(get_profile_service)) -> list[ProfileResponse]:
    profiles = await svc.list_profiles()
    return [ProfileResponse.model_validate(p) for p in profiles]


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    body: ProfileCreate,
    svc: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    profile = await svc.create_profile(body)
    return ProfileResponse.model_validate(profile)


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    svc: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    profile = await svc.get_profile(profile_id)
    return ProfileResponse.model_validate(profile)


@router.patch("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: str,
    body: ProfileUpdate,
    svc: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    profile = await svc.update_profile(profile_id, body)
    return ProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: str,
    svc: ProfileService = Depends(get_profile_service),
) -> None:
    await svc.delete_profile(profile_id)


@router.post("/{profile_id}/start", response_model=ProfileStatusResponse)
async def start_profile(
    profile_id: str,
    supervisor: GatewaySupervisor = Depends(get_gateway_supervisor),
) -> ProfileStatusResponse:
    return await supervisor.start_profile(profile_id)


@router.post("/{profile_id}/stop", response_model=ProfileStatusResponse)
async def stop_profile(
    profile_id: str,
    supervisor: GatewaySupervisor = Depends(get_gateway_supervisor),
) -> ProfileStatusResponse:
    return await supervisor.stop_profile(profile_id)


@router.get("/{profile_id}/status", response_model=ProfileStatusResponse)
async def profile_status(
    profile_id: str,
    supervisor: GatewaySupervisor = Depends(get_gateway_supervisor),
) -> ProfileStatusResponse:
    return await supervisor.refresh_status(profile_id)

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from src.api.daily_planning import ActionResponse, serialize_action
from src.api.dependencies import get_inbox_service
from src.application.inbox import InboxService
from src.domain.inbox import InboxItem

router = APIRouter(prefix="/inbox", tags=["inbox"])
ServiceDependency = Annotated[InboxService, Depends(get_inbox_service)]


class InboxItemResponse(BaseModel):
    id: UUID
    title: str
    created_at: str


class CreateInboxItemRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)


class UpdateInboxItemRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)


class ScheduleInboxItemRequest(BaseModel):
    date: date


def serialize_inbox_item(item: InboxItem) -> InboxItemResponse:
    return InboxItemResponse(
        id=item.id,
        title=item.title,
        created_at=item.created_at.isoformat(),
    )


@router.get("", response_model=list[InboxItemResponse])
def get_inbox(service: ServiceDependency) -> list[InboxItemResponse]:
    return [serialize_inbox_item(item) for item in service.get_inbox()]


@router.post("", response_model=InboxItemResponse, status_code=status.HTTP_201_CREATED)
def add_inbox_item(
    request: CreateInboxItemRequest,
    service: ServiceDependency,
) -> InboxItemResponse:
    return serialize_inbox_item(service.add_item(request.title))


@router.patch("/{item_id}", response_model=InboxItemResponse)
def rename_inbox_item(
    item_id: UUID,
    request: UpdateInboxItemRequest,
    service: ServiceDependency,
) -> InboxItemResponse:
    return serialize_inbox_item(service.rename_item(item_id, request.title))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inbox_item(item_id: UUID, service: ServiceDependency) -> None:
    service.delete_item(item_id)


@router.post("/{item_id}/schedule", response_model=ActionResponse)
def schedule_inbox_item(
    item_id: UUID,
    request: ScheduleInboxItemRequest,
    service: ServiceDependency,
) -> ActionResponse:
    return serialize_action(service.schedule_item(item_id, request.date))

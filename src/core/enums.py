from __future__ import annotations

from enum import StrEnum


class TaskStatus(StrEnum):
    REMOTE_ASSIGNED = "remote_assigned"
    LOCAL_CREATED = "local_created"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    RUNNING = "running"
    NEED_HUMAN_INPUT = "need_human_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SYNCED = "synced"


class TaskSource(StrEnum):
    TEAM_HUB = "team_hub"
    LOCAL = "local"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SyncBindingStatus(StrEnum):
    PENDING = "pending"
    SYNCED = "synced"
    ERROR = "error"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class TaskType(StrEnum):
    CODING_TASK = "coding_task"
    REVIEW_TASK = "review_task"
    DOC_TASK = "doc_task"
    RESEARCH_TASK = "research_task"
    WRITER_TASK = "writer_task"
    OPS_TASK = "ops_task"
    PROFILE_TASK = "profile_task"
    FINANCE_TASK = "finance_task"
    SALES_TASK = "sales_task"

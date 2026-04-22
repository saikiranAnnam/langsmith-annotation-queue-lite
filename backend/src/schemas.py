from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TracingProjectBase(BaseModel):
    name: str


class TracingProjectCreate(TracingProjectBase):
    pass


class TracingProject(TracingProjectBase):
    id: UUID
    created_at: datetime
    modified_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TraceBase(BaseModel):
    project_id: UUID
    inputs: dict | None = None
    outputs: dict | None = None
    trace_metadata: dict | None = None
    start_time: datetime
    end_time: datetime | None = None


class TraceCreate(TraceBase):
    pass


class Trace(TraceBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class TraceQueryRequest(BaseModel):
    trace_ids: list[UUID] | None = None
    project_id: UUID | None = None
    session_id: str | None = None


class QueueBase(BaseModel):
    name: str


class QueueCreate(QueueBase):
    pass


class QueueUpdate(BaseModel):
    name: str | None = None


class Queue(QueueBase):
    id: UUID
    created_at: datetime
    modified_at: datetime
    pending_count: int

    model_config = ConfigDict(from_attributes=True)


class QueueRubricItemBase(BaseModel):
    feedback_key: str
    description: str


class QueueRubricItemCreate(QueueRubricItemBase):
    pass


class QueueRubricItemUpdate(BaseModel):
    description: str | None = None


class QueueRubricItem(QueueRubricItemBase):
    id: UUID
    queue_id: UUID

    model_config = ConfigDict(from_attributes=True)


class QueuePopulateRequest(BaseModel):
    trace_ids: list[UUID]


class QueueEntryBase(BaseModel):
    trace_id: UUID
    queue_id: UUID


class QueueEntry(QueueEntryBase):
    id: UUID
    status: str
    added_at: datetime
    reserved_at: datetime | None = None
    reserved_by: str | None = None
    trace: Trace

    model_config = ConfigDict(from_attributes=True)


class FeedbackCreate(BaseModel):
    trace_id: UUID
    key: str
    score: float | None = None
    comment: str | None = None
    span_path: list[str | int] | None = None
    span_start_index: int | None = None
    span_end_index: int | None = None


class FeedbackUpdate(BaseModel):
    score: float | None = None
    comment: str | None = None
    span_path: list[str | int] | None = None
    span_start_index: int | None = None
    span_end_index: int | None = None


class Feedback(BaseModel):
    id: UUID
    trace_id: UUID
    key: str
    score: float | None = None
    comment: str | None = None
    span_path: list[str | int] | None = None
    span_start_index: int | None = None
    span_end_index: int | None = None
    created_at: datetime
    modified_at: datetime

    model_config = ConfigDict(from_attributes=True)

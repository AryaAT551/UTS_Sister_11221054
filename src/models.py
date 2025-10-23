from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid

# ======================
# Model: Event
# ======================
class Event(BaseModel):
    topic: str = Field(..., description="Topic name, e.g., 'user.created'")
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the event"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event creation time in ISO8601 UTC format"
    )
    source: str = Field(..., description="Name of the event source, e.g., 'user_service'")
    payload: Dict[str, Any] = Field(..., description="Event data payload (JSON object)")

    # ======================
    # Validators
    # ======================
    @field_validator("timestamp", mode="before")
    def ensure_utc_timestamp(cls, v):
        """Pastikan timestamp memiliki timezone UTC"""
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc)
        elif isinstance(v, datetime):
            return v.astimezone(timezone.utc)
        raise ValueError("Invalid timestamp format")

    @field_validator("topic", "source")
    def non_empty_string(cls, v, field):
        """Validasi agar topic dan source tidak kosong"""
        if not v.strip():
            raise ValueError(f"{field.name} cannot be empty")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic": "user.created",
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2023-10-23T10:00:00Z",
                "source": "user_service",
                "payload": {"user_id": "123", "email": "user@example.com"}
            }
        }
    )

# ======================
# Model: EventBatch
# ======================
class EventBatch(BaseModel):
    events: List[Event] = Field(..., description="List of events to publish")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "events": [
                    {
                        "topic": "order.placed",
                        "event_id": "e7c9c210-8f2f-4c84-b3e4-90a2e7f2b9b4",
                        "timestamp": "2023-10-23T12:00:00Z",
                        "source": "order_service",
                        "payload": {"order_id": "A123", "amount": 250000}
                    },
                    {
                        "topic": "order.shipped",
                        "event_id": "f0d1b9a3-9a1e-4a87-a4b3-10a8f0f2a111",
                        "timestamp": "2023-10-23T12:05:00Z",
                        "source": "shipment_service",
                        "payload": {"order_id": "A123", "status": "shipped"}
                    }
                ]
            }
        }
    )

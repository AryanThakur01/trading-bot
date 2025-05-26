from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime


class TimestampMixin(SQLModel):
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        nullable=False
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        nullable=False
    )


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sub: str = Field(index=True, unique=True)
    password: str

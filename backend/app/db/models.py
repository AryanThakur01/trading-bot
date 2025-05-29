from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime, timedelta


class TimestampMixin(SQLModel):
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, nullable=False
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, nullable=False
    )


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sub: str = Field(index=True, unique=True)


class OTP(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, nullable=False)
    otp: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=10),
        nullable=False,
        index=True,
    )

from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    type_notification: str
    message: str
    lien: str | None
    lue: bool
    date_creation: datetime

    class Config:
        from_attributes = True


class NotificationsOut(BaseModel):
    non_lues: int
    notifications: list[NotificationOut]
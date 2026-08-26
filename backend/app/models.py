from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    revision: str


class MessageResponse(BaseModel):
    message: str

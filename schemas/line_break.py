from typing import Literal

from pydantic import BaseModel

class LineBreakRequest(BaseModel):
    text: str

class LineBreakEqualsExportRequest(BaseModel):
    text: str
    align: Literal["left", "center", "right"] = "center"

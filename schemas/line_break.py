from pydantic import BaseModel

class LineBreakRequest(BaseModel):
    text: str

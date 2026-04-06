from pydantic import BaseModel


class BibleGenerateRequest(BaseModel):
    text: str

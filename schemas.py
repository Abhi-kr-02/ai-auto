from pydantic import BaseModel

class InboundMessage(BaseModel):
    phone: str
    text: str

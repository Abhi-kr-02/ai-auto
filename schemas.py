from pydantic import BaseModel
from typing import Optional

class InboundMessage(BaseModel):
    phone_number: str
    contact_name: Optional[str] = None
    message_text: str
    channel: str = "whatsapp_web"
    company_id: Optional[str] = None
    
    # For backward compatibility, also accept old field names
    phone: Optional[str] = None
    text: Optional[str] = None
    
    def __init__(self, **data):
        # Map old field names to new ones
        if 'phone' in data and 'phone_number' not in data:
            data['phone_number'] = data['phone']
        if 'text' in data and 'message_text' not in data:
            data['message_text'] = data['text']
        super().__init__(**data)

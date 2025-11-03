from pydantic import BaseModel 
from typing import Optional 
from uuid import UUID 
    
class Unavailability(BaseModel): 
    id: Optional[UUID] = None
    resource_id: UUID 
    external_id: UUID
    start_time: str
    end_time: str
    reason: str
    description: str
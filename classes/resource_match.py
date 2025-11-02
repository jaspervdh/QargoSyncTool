from pydantic import BaseModel 
from typing import Dict, Optional 
from uuid import UUID 
    
class ResourceMatch(BaseModel): 
    internal_id: UUID
    external_id: Optional[UUID]
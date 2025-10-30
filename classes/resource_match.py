from pydantic import BaseModel 
from typing import Dict, Optional 
import uuid 
    
class ResourceMatch(BaseModel): 
    internal_id: uuid.UUID
    external_id: Optional[uuid.UUID]
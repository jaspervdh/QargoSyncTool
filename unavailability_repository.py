# unavailability_repository.py
from typing import List, Dict, Optional
from uuid import UUID
from classes.unavailability import Unavailability
from qargo_client import QargoClient
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class UnavailabilityRepository:
    """Repository for managing unavailability data and CRUD operations."""
    
    def __init__(self, client: QargoClient, internal: bool = False):
        self.client = client
        self.internal = internal
    
    def get_all_for_resource(self, resource_id: UUID, start_time: datetime = None, end_time: datetime = None) -> List[Unavailability]:
        """Fetch all unavailabilities for a resource and convert to domain objects."""
        data = self.client.get_unavailabilities(resource_id, start_time, end_time)
        return [
            Unavailability(
                id=item["id"],
                resource_id=resource_id,
                external_id=item["external_id"] if self.internal else item["id"], 
                start_time=item["start_time"],
                end_time=item["end_time"],
                reason=item.get("reason", ""),
                description=item.get("description", "")
            )
            for item in data
        ]
    
    def create(self, unavailability: Unavailability) -> Unavailability:
        """Create a new unavailability."""
        result = self.client.create_unavailability(unavailability)
        unavailability.id = result.get("id")  # Update with API-assigned ID
        return unavailability
    
    def update(self, unavailability: Unavailability) -> Unavailability:
        """Update an existing unavailability."""
        if not unavailability.id:
            raise ValueError("Cannot update unavailability without ID")
        
        self.client.update_unavailability(unavailability)
        return unavailability
    
    def delete(self, resource_id: UUID, unavailability_id: UUID) -> bool:
        """Delete an unavailability."""
        return self.client.delete_unavailability(resource_id, unavailability_id)
    
    def build_lookup_map(self, unavailabilities: List[Unavailability]) -> Dict[tuple, Unavailability]:
        """
        Build a lookup map keyed by (internal_id, start_time, end_time).
        This represents the unique constraint for unavailabilities.
        """
        return {
            (u.resource_id, u.start_time, u.end_time): u 
            for u in unavailabilities
        }
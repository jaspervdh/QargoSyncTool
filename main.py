from datetime import datetime, timezone
import os
import logging
from typing import Dict
from uuid import UUID
from dotenv import load_dotenv
from classes.unavailability import Unavailability
from qargo_auth import QargoAuth
from qargo_client import QargoClient
from resource_matcher import ResourceMatcher
from unavailability_repository import UnavailabilityRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

 
class ResourceSyncService:
    """Service for synchronizing resources between local and master data systems."""
    
    def __init__(self, local_client: QargoClient, master_client: QargoClient):
        self.local_repo = UnavailabilityRepository(local_client, internal=True)
        self.master_repo = UnavailabilityRepository(master_client, internal=False)
        local_resources = self.local_repo.client.get_resources()
        master_resources = self.master_repo.client.get_resources()        
        matcher = ResourceMatcher(master_resources)
        self.resource_matches = matcher.match_all(local_resources)
            
    def _unavailability_needs_update(self, local: Unavailability, master: Unavailability) -> bool:
        """Check if fields other than the key fields have changed."""
        id_match = local.external_id == master.external_id
        changed = (
            local.start_time != master.start_time or
            local.end_time != master.end_time or
            local.reason != master.reason or 
            local.description != master.description
        )
        
        return id_match and changed
    
    def sync_unavailabilities_for_resource(self, internal_id: UUID, external_id: UUID) -> Dict[str, int]:
        """
        Sync unavailabilities for a single resource.
        Returns stats: created, updated, deleted, unchanged counts
        """
        stats = {"created": 0, "updated": 0, "deleted": 0, "unchanged": 0}
        
        start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        # Fetch from both APIs
        local_unavails = self.local_repo.get_all_for_resource(internal_id, start_time)
        master_unavails = self.master_repo.get_all_for_resource(external_id, start_time)
        
        # Match unavailabilities using the improved matcher
        matched_pairs = []
        unmatched_local = list(local_unavails)
        unmatched_master = list(master_unavails)
        
        # Find matches 
        for master_unavail in list(unmatched_master):
            for local_unavail in list(unmatched_local):
                if local_unavail.external_id == master_unavail.id:
                    matched_pairs.append((local_unavail, master_unavail))
                    unmatched_master.remove(master_unavail)
                    unmatched_local.remove(local_unavail)
                    break
        
        # CREATE (in master but not matched in local)
        for master_unavail in unmatched_master:
            master_unavail.resource_id = internal_id
            response = self.local_repo.create(master_unavail)
            master_unavail.id = response.id
            stats["created"] += 1
            logger.debug(f"Created unavailability: {master_unavail.start_time} - {master_unavail.end_time}")
        
        # UPDATE (matched pairs that need updates)
        for local_unavail, master_unavail in matched_pairs:
            if self._unavailability_needs_update(local_unavail, master_unavail):
                self.local_repo.update(master_unavail)
                stats["updated"] += 1
                logger.debug(f"Updated unavailability: {local_unavail.id}")
            else:
                stats["unchanged"] += 1
        
        # DELETE (in local but not matched in master)
        for local_unavail in unmatched_local:
            if local_unavail.id:
                self.local_repo.delete(internal_id, local_unavail.id)
                stats["deleted"] += 1
                logger.debug(f"Deleted unavailability: {local_unavail.id}")
        
        return stats

    def sync_unavailabilities(self):
        """Sync unavailabilities from master to local system for all resource matches."""
        if not self.resource_matches:
            raise ValueError("Must call match_resources() first")
        
        total_stats = {"created": 0, "updated": 0, "deleted": 0, "unchanged": 0, "errors": 0}
        
        for local_id, master_id in self.resource_matches.items():
            try:
                stats = self.sync_unavailabilities_for_resource(local_id, master_id)
                
                # Aggregate stats
                for key in ["created", "updated", "deleted", "unchanged"]:
                    total_stats[key] += stats[key]
                    
            except Exception as e:
                logger.error(f"Failed to sync unavailabilities for resource {local_id}: {e}")
                total_stats["errors"] += 1
                continue
        
        logger.info(f"Sync complete: {total_stats}")
        return total_stats

    def run(self):
        """Run the complete synchronization workflow."""
        return self.sync_unavailabilities()


def main():
    """Entry point for the resource synchronization tool."""
    load_dotenv()
    
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    master_data_client_id = os.getenv("MASTER_DATA_CLIENT_ID")
    master_data_client_secret = os.getenv("MASTER_DATA_CLIENT_SECRET")
    
    if not all([client_id, client_secret, master_data_client_id, master_data_client_secret]):
        logger.error("Missing required environment variables")
        raise ValueError("CLIENT_ID, CLIENT_SECRET, MASTER_DATA_CLIENT_ID, and MASTER_DATA_CLIENT_SECRET must be set")
    
    logger.info("Authenticating with Qargo API...")
    local_auth = QargoAuth(client_id=client_id, client_secret=client_secret)
    master_auth = QargoAuth(client_id=master_data_client_id, client_secret=master_data_client_secret)
    
    local_token = local_auth.get_token()
    master_token = master_auth.get_token()
    
    with QargoClient(local_token) as local_client, \
         QargoClient(master_token) as master_client:
        
        service = ResourceSyncService(local_client, master_client)
        service.run()
        
if __name__ == "__main__":
    main()
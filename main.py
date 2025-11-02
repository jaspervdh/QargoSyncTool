import os
import logging
from dotenv import load_dotenv

from qargo_auth import QargoAuth
from qargo_client import QargoClient
from resource_matcher import ResourceMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class ResourceSyncService:
    """Service for synchronizing resources between local and master data systems."""
    
    def __init__(self, local_client: QargoClient, master_client: QargoClient):
        self.local_client = local_client
        self.master_client = master_client
    
    def sync_resources(self):
        """
        Main synchronization flow:
        1. Fetch resources from both systems
        2. Match local resources to master resources
        3. Return matched resource mappings
        """
        logger.info("Starting resource synchronization...")
        
        try:
            # Fetch resources from both systems
            local_resources = self.local_client.get_resources()
            master_resources = self.master_client.get_resources()
            
            # Match resources
            matcher = ResourceMatcher(master_resources)
            matches = matcher.match_all(local_resources)
            
            # Log summary
            matched_count = sum(1 for m in matches if m.external_id)
            unmatched_count = len(matches) - matched_count
            
            logger.info(f"Synchronization complete: {matched_count} matched, {unmatched_count} unmatched")
            
            return matches
            
        except Exception as e:
            logger.error(f"Resource synchronization failed: {e}", exc_info=True)
            raise


def main():
    """Entry point for the resource synchronization tool."""
    # load and validate environment variables
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    master_data_client_id = os.getenv("MASTER_DATA_CLIENT_ID")
    master_data_client_secret = os.getenv("MASTER_DATA_CLIENT_SECRET")
    
    if not all([client_id, client_secret, master_data_client_id, master_data_client_secret]):
        logger.error("Missing required environment variables")
        raise ValueError("CLIENT_ID, CLIENT_SECRET, MASTER_DATA_CLIENT_ID, and MASTER_DATA_CLIENT_SECRET must be set")
    
    # auth and create clients
    logger.info("Authenticating with Qargo API...")
    local_auth = QargoAuth(client_id=client_id, client_secret=client_secret)
    master_auth = QargoAuth(client_id=master_data_client_id, client_secret=master_data_client_secret)
    
    local_token = local_auth.get_token()
    master_token = master_auth.get_token()
    
    # context managers for proper resource cleanup
    with QargoClient(local_token) as local_client, \
         QargoClient(master_token) as master_client:
        
        # Run synchronization
        service = ResourceSyncService(local_client, master_client)
        matches = service.sync_resources()


if __name__ == "__main__":
    main()
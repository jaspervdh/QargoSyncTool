import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class QargoClient:
    """Client for interacting with the Qargo API."""
    
    BASE_URL = "https://api.qargo.io/v1"
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_token}"})
    
    def get_resources(self) -> list[dict]:
        """
        Fetch all resources from the API using cursor-based pagination.
        
        Returns:
            List of resource dictionaries
            
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.BASE_URL}/resources/resource"
        resources = []
        cursor: Optional[str] = None
        
        try:
            while True:
                params = {"cursor": cursor} if cursor else {}
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                resources.extend(data.get("items", []))
                
                cursor = data.get("next_cursor")
                if not cursor:
                    break
            
            logger.info(f"Retrieved {len(resources)} resources from API")
            return resources
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch resources: {e}")
            raise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
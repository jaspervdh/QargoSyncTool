import logging
import requests
from typing import Optional
from uuid import UUID
from classes.unavailability import Unavailability

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
    
    def get_unavailabilities(self, resource_id: UUID):
        """
        Fetch all unavailabilities of a resources from the API using cursor-based pagination.
        
        Args:
            resource_id (str): UUID of the resource whose unavailabilities should be fetched.            
        Returns:
            List of unavailabilities dictionaries
            
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.BASE_URL}/resources/resource/{resource_id}/unavailability"
        unavailabilities = []
        cursor: Optional[str] = None 
        
        try:
            while True:
                params = {"cursor": cursor} if cursor else {}
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                unavailabilities.extend(data.get("items", []))
                
                cursor = data.get("next_cursor")
                if not cursor:
                    break
            
            logger.info(f"Retrieved {len(unavailabilities)} unavailabilities from API")
            return unavailabilities
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch unavailabilities: {e}")
            raise
        
    def create_unavailability(self, unavailability: Unavailability):
        url = f"{self.BASE_URL}/resources/resource/{unavailability.internal_id}/unavailability"
        
        payload = {
            "start_time": unavailability.start_time,
            "end_time": unavailability.end_time,
            "reason": unavailability.reason,
            "description": unavailability.description
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Created unavailability for resource {unavailability.internal_id}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to create unavailability: {e}")
            raise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
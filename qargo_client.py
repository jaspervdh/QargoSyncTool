import logging
from datetime import datetime
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
    
    def _paginated_get(self, url: str, params: dict = None) -> list[dict]:
        """
        Fetch all items from a paginated API endpoint.
        
        Args:
            url (str): API endpoint URL
            params (dict, optional): Additional query parameters 
            
        Returns:
            List of all items from paginated response
            
        Raises:
            requests.RequestException: If API request fails
        """
        items = []
        cursor: Optional[str] = None
        base_params = params or {}
        
        try:
            while True:
                request_params = {**base_params, "cursor": cursor} if cursor else base_params
                response = self.session.get(url, params=request_params)
                response.raise_for_status()
                
                data = response.json()
                items.extend(data.get("items", []))
                cursor = data.get("next_cursor")
                
                if not cursor:
                    break
            
            return items
        except requests.RequestException as e:
            logger.error(f"Failed to fetch from {url}: {e}")
            raise

    def get_resources(self) -> list[dict]:
        """
        Fetch all resources from the API using cursor-based pagination.
        
        Returns:
            List of resource dictionaries
            
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.BASE_URL}/resources/resource"
        resources = self._paginated_get(url)
        logger.info(f"Retrieved {len(resources)} resources from API")
        return resources

    def get_unavailabilities(self, resource_id: UUID, start_time: datetime = None, end_time: datetime = None) -> list[dict]:
        """
        Fetch all unavailabilities of a resource from the API using cursor-based pagination.
        
        Args:
            resource_id (UUID): UUID of the resource whose unavailabilities should be fetched.
            start_time (datetime, optional): Filter to fetch unavailabilities after this time.
            end_time (datetime, optional): Filter to fetch unavailabilities before this time.
                        
        Returns:
            List of unavailability dictionaries
            
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.BASE_URL}/resources/resource/{resource_id}/unavailability"
        
        params = {
            "start_time": start_time,
            "end_time": end_time
        }
        
        unavailabilities = self._paginated_get(url, params)
        logger.info(f"Retrieved {len(unavailabilities)} unavailabilities for resource {resource_id}")
        return unavailabilities
        
    def create_unavailability(self, unavailability: Unavailability) -> dict:
        url = f"{self.BASE_URL}/resources/resource/{unavailability.resource_id}/unavailability"
        
        payload = {
            "external_id": str(unavailability.external_id),
            "start_time": unavailability.start_time,
            "end_time": unavailability.end_time,
            "reason": unavailability.reason,
            "description": unavailability.description
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Created unavailability for resource {unavailability.resource_id}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to create unavailability: {e}")
            raise
            
    def update_unavailability(self, unavailability: Unavailability) -> dict:
        if not unavailability.id:
            raise ValueError("Cannot update unavailability without an ID")

        url = f"{self.BASE_URL}/resources/resource/{unavailability.resource_id}/unavailability/{unavailability.id}"
        payload = {
            "start_time": unavailability.start_time,
            "end_time": unavailability.end_time,
            "reason": unavailability.reason,
            "description": unavailability.description
        }
        if unavailability.external_id:
            payload["external_id"] = str(unavailability.external_id)

        try:
            response = self.session.put(url, json=payload)
            response.raise_for_status()
            logger.info(f"Updated unavailability {unavailability.id} for resource {unavailability.resource_id}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to update unavailability: {e}")
            raise

    def _delete_item(self, url: str, item_id: UUID) -> None:
        url = f"{url}/{item_id}"
        
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            logger.info(f"Deleted item with id {item_id}")
        except requests.RequestException as e:
            logger.error(f"Failed to delete item: {e}")
            raise
    
    def delete_unavailability(self, resource_id: UUID, unavailability_id: UUID) -> None:
        url = f"{self.BASE_URL}/resources/resource/{resource_id}/unavailability"
        self._delete_item(url, unavailability_id)
        logger.info(f"Deleted unavailability {unavailability_id} for resource {resource_id}")


    def get(self, url):
        res = self.session.get(url)
        print(res)
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
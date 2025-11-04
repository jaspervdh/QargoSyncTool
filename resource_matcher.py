import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ResourceMatcher:
    """Matches local resources with master data resources based on various identifiers."""
    
    def __init__(self, master_resources: list[dict]):
        self.master_resources = master_resources
        
    def find_match(self, local_resource: dict) -> Optional[str]:
        """
        Compare a local resource against master resources to find a match.
        
        Matching strategy (in priority order):
        1. Custom fields: employeenumber or fleetno
        2. License plate: truck, van, or tractor
        3. Name: normalized case-insensitive comparison
        
        Args:
            local_resource: The local resource dictionary to match
            
        Returns:
            The ID of the matching master resource, or None if no match found
        """
        match_id = (
            self._match_by_custom_fields(local_resource)
            or self._match_by_license_plate(local_resource)
            or self._match_by_name(local_resource)
        )
        
        if not match_id:
            logger.warning(
                f"No match found for resource: id={local_resource.get('id')}, "
                f"name={local_resource.get('name', 'N/A')}"
            )
        
        return match_id
    
    def _match_by_custom_fields(self, local: dict) -> Optional[str]:
        """Match by employeenumber or fleetno custom fields."""
        cf_local = local.get("custom_fields", {})
        
        for master in self.master_resources:
            cf_master = master.get("custom_fields", {})
            
            # Match by employee number
            if cf_local.get("employeenumber") and cf_local["employeenumber"] == cf_master.get("employeenumber"):
                logger.debug(f"Matched by employeenumber: {cf_local['employeenumber']}")
                return master.get("id")
            
            # Match by fleet number
            if cf_local.get("fleetno") and cf_local["fleetno"] == cf_master.get("fleetno"):
                logger.debug(f"Matched by fleetno: {cf_local['fleetno']}")
                return master.get("id")
        
        return None
    
    def _match_by_license_plate(self, local: dict) -> Optional[str]:
        """Match by license plate for truck, van, or tractor."""
        for key in ("truck", "van", "tractor"):
            if key not in local or not local[key].get("license_plate"):
                continue
                
            lp_local = local[key]["license_plate"].replace(" ", "").lower()
            
            for master in self.master_resources:
                if key in master and master[key].get("license_plate"):
                    lp_master = master[key]["license_plate"].replace(" ", "").lower()
                    if lp_local == lp_master:
                        logger.debug(f"Matched by {key} license plate: {lp_local}")
                        return master.get("id")
        
        return None
    
    def _match_by_name(self, local: dict) -> Optional[str]:
        """Match by normalized name (case-insensitive, whitespace-trimmed)."""
        name_local = local.get("name", "").strip().lower()
        
        if not name_local:
            return None
        
        for master in self.master_resources:
            name_master = master.get("name", "").strip().lower()
            if name_local == name_master:
                logger.debug(f"Matched by name: {name_local}")
                return master.get("id")
        
        return None
    
    def match_all(self, local_resources: list[dict]) -> dict:
        """
        Match all local resources against master resources.
        
        Args:
            local_resources: List of local resource dictionaries
            
        Returns:
            Dictionary mapping local resource IDs to matched resource IDs from external API       
        """
        matches = {}
        
        for resource in local_resources:
            match_id = self.find_match(resource)
            if match_id: 
                matches[resource["id"]] = match_id
        
        logger.info(
            f"Matched {len(matches)} out of {len(local_resources)} resources"
        )
        
        return matches
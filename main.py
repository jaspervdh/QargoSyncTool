import os
import logging

from pprint import pprint
import requests
from dotenv import load_dotenv
from qargo_auth import QargoAuth

from classes.resource_match import ResourceMatch

logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
MASTER_DATA_CLIENT_ID = os.getenv("MASTER_DATA_CLIENT_ID")
MASTER_DATA_CLIENT_SECRET = os.getenv("MASTER_DATA_CLIENT_SECRET")


qargo_auth = QargoAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
own_api_token = qargo_auth.get_token()

master_data_auth = QargoAuth(client_id=MASTER_DATA_CLIENT_ID, client_secret=MASTER_DATA_CLIENT_SECRET)
master_data_api_token = master_data_auth.get_token()

def get_resources(api_token):
    resources_url = "https://api.qargo.io/v1/resources/resource"
    headers = {"Authorization": f"Bearer {api_token}"}
    cursor = None
    recourses = []
    
    while True:
        response = requests.get(resources_url, headers=headers, params={"cursor": cursor})
        data = response.json()
        recourses += data["items"]
        cursor = data.get("next_cursor", None)
        
        if not cursor:
            return recourses
        
def find_match(local, master_list):
    "compare resources on custom_field and name attributes to find matches"
    cf_local = local.get("custom_fields", {})
    name_local = local.get("name", "").strip().lower()

    # Match by employee number or fleetno
    for m in master_list:
        cf_master = m.get("custom_fields", {})
        if cf_local.get("employeenumber") and cf_local["employeenumber"] == cf_master.get("employeenumber"):
            return m.get("id")
        if cf_local.get("fleetno") and cf_local["fleetno"] == cf_master.get("fleetno"):
            return m.get("id")

    # Match by license plate (truck/van/tractor)
    for key in ("truck", "van", "tractor"):
        if key in local and local[key].get("license_plate"):
            lp = local[key]["license_plate"].replace(" ", "").lower()
            for m in master_list:
                if key in m and m[key].get("license_plate", "").replace(" ", "").lower() == lp:
                    return m.get("id")

    # Match by normalized name (last resort)
    for m in master_list:
        if name_local == m.get("name", "").strip().lower():
            return m.get("id")

    return None

own_resources = get_resources(own_api_token)
master_resources= get_resources(master_data_api_token)

def match_resources(local_resources, master_resources):

    matches: list[ResourceMatch] = []
    for recourse in local_resources:
        match_id = find_match(recourse, master_resources)
        if not match_id:
            logger.warning(f"No match found for resourece with id: {recourse["id"]}")
        match = ResourceMatch(internal_id=recourse["id"], external_id=match_id)
        matches.append(match)
    return matches

matches = match_resources(own_resources, master_resources)
print(matches[:10])



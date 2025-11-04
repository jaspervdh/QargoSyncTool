import json
import os
import time
import base64
import requests
import logging
from datetime import datetime

AUTH_URL = "https://api.qargo.com/v1/auth/token"
TOKEN_CACHE_FILE = ".qargo_token.json" 
TOKEN_REFRESH_BUFFER = 60

logger = logging.getLogger(__name__)

class QargoAuth:
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expiry_time = 0
        
    def get_token(self):
        # persitent cache of token to prevent req. every time code runs/a new QargoAuth object is made
        self._load_cached_token()
        
        if not self.token or time.time() >= self.token_expiry_time:
            self._fetch_token()
            self._save_cached_token()
        return self.token
    
    def _fetch_token(self):
        credentials = f"{self.client_id}:{self.client_secret}"
        credentials_bytes = credentials.encode() # encode string to bytes: string -> bytes
        encoded_credentials = base64.b64encode(credentials_bytes).decode() # bytes -> encoded bytes -> encoded string
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_credentials}"
        }
        
        response = requests.post(AUTH_URL, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Fetching API token failed: {response.status_code} - {response.text}")
        
        # unpack data (https://api.qargo.io/ca849acf3cb543a1975722a2882b7712/docs#tag/API-Authentication/operation/generate_token_v1_auth_token_post)
        data = response.json()
        
        try:
            self.token = data.get("access_token")
            expires_in = data.get("expires_in")
        except Exception as e:
            raise Exception(f"Error unpacking token response: {e}")    
        
        if not self.token:
            raise Exception(f"Token not available in data: {data}")    

        self.token_expiry_time = time.time() + expires_in - TOKEN_REFRESH_BUFFER
        logger.debug(f"Fetched new API token, expires on {datetime.fromtimestamp(self.token_expiry_time)}")
            
    def _save_cached_token(self):
            """Save the token and its expiry to disk."""
            try:
                cache = self._load_cache_file()
                
                # add token to cache json
                cache[self.client_id] = {
                    "token": self.token,
                    "token_expiry_time": self.token_expiry_time,
                }
                
                with open(TOKEN_CACHE_FILE, "w") as f:
                    json.dump(cache, f, indent=2)
                
                logger.debug(f"Token cached locally for client {self.client_id}")
            except Exception as e:
                logger.error(f"Could not write token cache: {e}")

    def _load_cached_token(self):
        """Try loading the token from a local cache. Checks its expiry."""
        try:
            cache = self._load_cache_file()
            
            # check if api key cached for client
            if self.client_id not in cache:
                return
            
            entry = cache[self.client_id]
            
            # get token and check if still valid
            if entry.get("token") and time.time() < entry.get("token_expiry_time", 0):
                self.token = entry["token"]
                self.token_expiry_time = entry["token_expiry_time"]
                logger.debug(f"Loaded valid cached token, expires on {datetime.fromtimestamp(self.token_expiry_time)}")
        except Exception as e:
            logger.warning(f"Failed to read cached token: {e}")
            
    def _load_cache_file(self):
        """Load the entire cache file, or return empty dict if it doesn't exist."""
        if not os.path.exists(TOKEN_CACHE_FILE):
            return {}
        
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.debug(f"Could not read cache file: {e}")
            return {}      
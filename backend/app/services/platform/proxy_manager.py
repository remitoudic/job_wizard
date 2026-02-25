import json
import random
import os
from typing import Optional, Dict, List
import logfire
from app.core.config import settings

class ProxyManager:
    _instance = None
    _proxies: List[Dict] = []
    _current_index: int = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProxyManager, cls).__new__(cls)
            cls._instance._load_proxies()
        return cls._instance

    def _load_proxies(self):
        """Load proxies from the JSON file specified in config"""
        try:
            # Handle relative path from config
            os.getcwd()
            # If running from root, it might be in backend/proxies.json
            # settings.PROXY_FILE_PATH is "proxies.json" by default, or "backend/proxies.json"
            
            # Try direct path first
            file_path = settings.PROXY_FILE_PATH
            if not os.path.exists(file_path):
                # Try prepending backend/ if we are in root
                file_path = os.path.join("backend", settings.PROXY_FILE_PATH)
            
            if not os.path.exists(file_path):
                # Final check if we are already in backend dir
                file_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", settings.PROXY_FILE_PATH)

            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    self._proxies = json.load(f)
                logfire.info(f"Loaded {len(self._proxies)} proxies from {file_path}")
            else:
                logfire.warn(f"Proxy file not found at {settings.PROXY_FILE_PATH}")
                self._proxies = []
                
        except Exception as e:
            logfire.error("Failed to load proxies", error=str(e))
            self._proxies = []

    def get_next_proxy(self) -> Optional[str]:
        """
        Get the next proxy in rotation.
        Returns IP:Port string formatted for Playwright/HTTPX
        """
        if not self._proxies:
            return None

        # Simple Round Robin
        proxy_data = self._proxies[self._current_index]
        self._current_index = (self._current_index + 1) % len(self._proxies)

        # Construct proxy string
        # Format: http://ip:port
        # Note: The provided JSON has ip and port fields
        try:
            ip = proxy_data.get("ip") or proxy_data.get("proxy_address")
            port = proxy_data.get("port")
            username = proxy_data.get("username")
            password = proxy_data.get("password")

            protocol = proxy_data.get("protocol", "http")

            if ip and port:
                if username and password:
                    return f"{protocol}://{username}:{password}@{ip}:{port}"
                return f"{protocol}://{ip}:{port}"
        except Exception as e:
            logfire.error("Error formatting proxy", error=str(e), data=proxy_data)
        
        return None

    def get_random_proxy(self) -> Optional[str]:
        """Get a random proxy from the list"""
        if not self._proxies:
            return None
        
        proxy_data = random.choice(self._proxies)
        try:
            ip = proxy_data.get("ip") or proxy_data.get("proxy_address")
            port = proxy_data.get("port")
            username = proxy_data.get("username")
            password = proxy_data.get("password")

            protocol = proxy_data.get("protocol", "http")

            if ip and port:
                if username and password:
                    return f"{protocol}://{username}:{password}@{ip}:{port}"
                return f"{protocol}://{ip}:{port}"
        except Exception:
            return None
        return None

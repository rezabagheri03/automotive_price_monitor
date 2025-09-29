"""
Proxy management and rotation utilities
"""
import random
import logging
import time
import requests
from typing import List, Optional, Dict
from urllib.parse import urlparse
from config.settings import Config
from .logger import setup_logger

logger = setup_logger(__name__)


class ProxyManager:
    """Manage proxy rotation and validation"""
    
    def __init__(self):
        self.config = Config()
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = []
        self.current_index = 0
        self.last_rotation = 0
        self.rotation_interval = 300  # 5 minutes
        
        if self.config.PROXY_ENABLED:
            self._load_proxies()
            self._validate_proxies()
    
    def _load_proxies(self):
        """Load proxies from configuration"""
        if not self.config.PROXY_LIST:
            logger.warning("Proxy enabled but no proxy list provided")
            return
        
        self.proxies = []
        for proxy_str in self.config.PROXY_LIST:
            proxy_str = proxy_str.strip()
            if proxy_str:
                proxy_info = self._parse_proxy(proxy_str)
                if proxy_info:
                    self.proxies.append(proxy_info)
        
        logger.info(f"Loaded {len(self.proxies)} proxies")
    
    def _parse_proxy(self, proxy_str: str) -> Optional[Dict]:
        """Parse proxy string into components"""
        try:
            # Handle different proxy formats
            if '@' in proxy_str:
                # Format: username:password@host:port
                auth_part, host_part = proxy_str.split('@')
                username, password = auth_part.split(':')
                host, port = host_part.split(':')
            else:
                # Format: host:port
                host, port = proxy_str.split(':')
                username, password = None, None
            
            return {
                'host': host.strip(),
                'port': int(port.strip()),
                'username': username.strip() if username else None,
                'password': password.strip() if password else None,
                'url': f"http://{proxy_str}",
                'failures': 0,
                'last_used': 0,
                'response_time': 0
            }
            
        except Exception as e:
            logger.error(f"Error parsing proxy {proxy_str}: {e}")
            return None
    
    def _validate_proxies(self):
        """Validate all proxies and categorize them"""
        logger.info("Validating proxies...")
        
        self.working_proxies = []
        self.failed_proxies = []
        
        test_urls = [
            'http://httpbin.org/ip',
            'https://api.ipify.org?format=json',
            'http://ip-api.com/json'
        ]
        
        for proxy in self.proxies:
            is_working = False
            
            for test_url in test_urls:
                if self._test_proxy(proxy, test_url):
                    is_working = True
                    break
            
            if is_working:
                self.working_proxies.append(proxy)
                logger.debug(f"Proxy {proxy['host']}:{proxy['port']} is working")
            else:
                self.failed_proxies.append(proxy)
                logger.warning(f"Proxy {proxy['host']}:{proxy['port']} failed validation")
        
        logger.info(f"Proxy validation completed: {len(self.working_proxies)} working, {len(self.failed_proxies)} failed")
    
    def _test_proxy(self, proxy: Dict, test_url: str, timeout: int = 10) -> bool:
        """Test if a proxy is working"""
        try:
            start_time = time.time()
            
            proxy_dict = {
                'http': proxy['url'],
                'https': proxy['url']
            }
            
            response = requests.get(
                test_url,
                proxies=proxy_dict,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            if response.status_code == 200:
                response_time = time.time() - start_time
                proxy['response_time'] = response_time
                return True
            else:
                return False
                
        except Exception as e:
            logger.debug(f"Proxy test failed for {proxy['host']}:{proxy['port']}: {e}")
            return False
    
    def get_proxy(self) -> Optional[Dict]:
        """Get next working proxy"""
        if not self.working_proxies:
            return None
        
        # Check if we need to rotate
        current_time = time.time()
        if current_time - self.last_rotation > self.rotation_interval:
            self._rotate_proxy()
            self.last_rotation = current_time
        
        # Get current proxy
        if self.current_index < len(self.working_proxies):
            proxy = self.working_proxies[self.current_index]
            proxy['last_used'] = current_time
            return proxy
        else:
            self.current_index = 0
            return self.working_proxies[0] if self.working_proxies else None
    
    def _rotate_proxy(self):
        """Rotate to next proxy"""
        if len(self.working_proxies) > 1:
            self.current_index = (self.current_index + 1) % len(self.working_proxies)
            current_proxy = self.working_proxies[self.current_index]
            logger.debug(f"Rotated to proxy: {current_proxy['host']}:{current_proxy['port']}")
    
    def get_random_proxy(self) -> Optional[Dict]:
        """Get a random working proxy"""
        if not self.working_proxies:
            return None
        
        return random.choice(self.working_proxies)
    
    def mark_proxy_failed(self, proxy: Dict):
        """Mark a proxy as failed and potentially remove it"""
        if proxy in self.working_proxies:
            proxy['failures'] += 1
            
            # If too many failures, move to failed list
            if proxy['failures'] >= 3:
                self.working_proxies.remove(proxy)
                self.failed_proxies.append(proxy)
                logger.warning(f"Proxy {proxy['host']}:{proxy['port']} moved to failed list")
                
                # Adjust current index if needed
                if self.current_index >= len(self.working_proxies):
                    self.current_index = 0
    
    def get_proxy_for_scrapy(self) -> Optional[str]:
        """Get proxy in format suitable for Scrapy"""
        proxy = self.get_proxy()
        if not proxy:
            return None
        
        if proxy['username'] and proxy['password']:
            return f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        else:
            return f"http://{proxy['host']}:{proxy['port']}"
    
    def get_proxy_for_requests(self) -> Optional[Dict]:
        """Get proxy in format suitable for requests library"""
        proxy = self.get_proxy()
        if not proxy:
            return None
        
        proxy_url = proxy['url']
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def get_stats(self) -> Dict:
        """Get proxy statistics"""
        return {
            'total_proxies': len(self.proxies),
            'working_proxies': len(self.working_proxies),
            'failed_proxies': len(self.failed_proxies),
            'current_proxy_index': self.current_index,
            'proxy_enabled': self.config.PROXY_ENABLED,
            'rotation_interval': self.rotation_interval,
            'last_rotation': self.last_rotation
        }
    
    def refresh_failed_proxies(self):
        """Re-test failed proxies and move working ones back"""
        if not self.failed_proxies:
            return
        
        logger.info(f"Re-testing {len(self.failed_proxies)} failed proxies...")
        
        recovered_proxies = []
        
        for proxy in self.failed_proxies[:]:  # Copy list to avoid modification during iteration
            if self._test_proxy(proxy, 'http://httpbin.org/ip'):
                proxy['failures'] = 0  # Reset failure count
                recovered_proxies.append(proxy)
                self.failed_proxies.remove(proxy)
                self.working_proxies.append(proxy)
        
        if recovered_proxies:
            logger.info(f"Recovered {len(recovered_proxies)} proxies")
    
    def get_best_proxy(self) -> Optional[Dict]:
        """Get proxy with best response time"""
        if not self.working_proxies:
            return None
        
        # Sort by response time (ascending) and failures (ascending)
        best_proxy = min(
            self.working_proxies,
            key=lambda p: (p.get('response_time', 999), p.get('failures', 0))
        )
        
        return best_proxy
    
    def cleanup_old_proxies(self, max_age_hours: int = 24):
        """Remove proxies that haven't been used for a long time"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        old_proxies = [
            proxy for proxy in self.working_proxies
            if current_time - proxy.get('last_used', 0) > max_age_seconds
        ]
        
        for proxy in old_proxies:
            self.working_proxies.remove(proxy)
        
        if old_proxies:
            logger.info(f"Removed {len(old_proxies)} old unused proxies")
    
    def is_proxy_enabled(self) -> bool:
        """Check if proxy rotation is enabled and working"""
        return self.config.PROXY_ENABLED and len(self.working_proxies) > 0


# Create global proxy manager instance
proxy_manager = ProxyManager()
